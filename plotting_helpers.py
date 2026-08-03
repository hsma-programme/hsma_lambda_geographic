import matplotlib.pyplot as plt
import geopandas
from pyproj import Geod
import contextily as cx
from shapely.geometry import Point, LineString
from valhalla import Actor, get_config
import pandas as pd


def plot_route_comparison(
    start_coords,
    end_coords,
    start_name="Start",
    end_name="End",
    road_route=None,
    units="km",
    buffer=30_000,
    figsize=(10, 5),
):
    """
    Compare crow-flies and road route distances.

    Parameters
    ----------
    start_coords : tuple
        (longitude, latitude)
    end_coords : tuple
        (longitude, latitude)
    start_name : str
        Label for first point.
    end_name : str
        Label for second point.
    road_route : GeoDataFrame or str, optional
        Either:
            - GeoDataFrame containing LineString geometry
            - Path to a vector file (GeoJSON, GPKG, etc.)
    units : {"km", "miles"}
        Distance units.
    buffer : float
        Map buffer in metres (Web Mercator).
    figsize : tuple
        Figure size.

    Returns
    -------
    fig, axes
    """

    geod = Geod(ellps="WGS84")

    if units not in {"km", "miles"}:
        raise ValueError("units must be 'km' or 'miles'")

    # ------------------------------------------------------------------
    # Build geometries
    # ------------------------------------------------------------------

    points = geopandas.GeoDataFrame(
        {"name": [start_name, end_name]},
        geometry=[Point(start_coords), Point(end_coords)],
        crs="EPSG:4326",
    )

    straight = geopandas.GeoDataFrame(
        geometry=[LineString([start_coords, end_coords])],
        crs="EPSG:4326",
    )

    if isinstance(road_route, str):
        road_route = geopandas.read_file(road_route)

    points = points.to_crs(3857)
    straight = straight.to_crs(3857)

    if road_route is not None:
        road_route = road_route.to_crs(3857)

    # ------------------------------------------------------------------
    # Distances
    # ------------------------------------------------------------------

    _, _, crow_flies = geod.inv(
        start_coords[0],
        start_coords[1],
        end_coords[0],
        end_coords[1],
    )

    if units == "km":
        factor = 1000
        label = "km"
    else:
        factor = 1609.344
        label = "miles"

    crow_flies /= factor

    road_distance = None
    if road_route is not None:
        road_distance = (road_route.to_crs("EPSG:27700").length.sum()) / factor
        # road_distance = road_route.length.sum()

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------

    fig, axes = plt.subplots(
        1,
        2,
        figsize=figsize,
        sharex=True,
        sharey=True,
    )

    for ax in axes:
        points.plot(
            ax=ax,
            color="black",
            markersize=30,
            zorder=3,
        )

        for _, row in points.iterrows():
            ax.annotate(
                row["name"],
                (row.geometry.x, row.geometry.y),
                xytext=(5, 5),
                textcoords="offset points",
            )

    straight.plot(ax=axes[0], linewidth=3)

    if road_route is not None:
        road_route.plot(ax=axes[1], linewidth=3)

    axes[0].set_title("Straight line")
    axes[1].set_title("Road route")

    axes[0].text(
        0.03,
        0.97,
        f"Straight Line Distance: {crow_flies:.1f} {label}",
        transform=axes[0].transAxes,
        va="top",
        bbox=dict(facecolor="white", alpha=0.8),
    )

    if road_distance is not None:
        detour_factor = road_distance / crow_flies

        axes[1].text(
            0.03,
            0.97,
            (
                f"Distance: {road_distance:.1f} {label}\n"
                f"Detour factor: {detour_factor:.2f}×"
            ),
            transform=axes[1].transAxes,
            va="top",
            bbox=dict(facecolor="white", alpha=0.8),
        )

    for ax in axes:
        ax.set_axis_off()

        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()

        ax.set_xlim(xmin - buffer, xmax + buffer)
        ax.set_ylim(ymin - buffer, ymax + buffer)

        cx.add_basemap(ax)

    return fig, axes


def plot_isochrones(
    origins,
    mode="auto",
    contours=(10, 20, 30),
    actor=None,
    tile_dir="data/devon-260422_valhalla-modified-traffic_tiles",
    ax=None,
    colours=None,
    alpha=0.5,
    add_basemap=True,
    origin_kwargs=None,
    title=None,
):
    """
    Plot Valhalla isochrones.

    Parameters
    ----------
    origins : tuple or list of tuples
        (lon, lat) coordinate(s).
    mode : str
        Valhalla costing mode ("auto", "pedestrian", "bicycle", etc.)
    contours : iterable
        Travel time contours in minutes.
    actor : valhalla.Actor, optional
        Existing Valhalla actor.
    tile_dir : str
        Location of Valhalla tiles (only used if actor is None).
    ax : matplotlib Axes, optional
    colours : dict, optional
        Mapping of contour -> colour.
    alpha : float
    add_basemap : bool
    origin_kwargs : dict, optional
        Passed to origin plot.

    Returns
    -------
    GeoDataFrame
        Isochrone polygons.
    """

    if type(contours) == int:
        contours = [contours]

    if actor is None:
        config = get_config(
            tile_dir=tile_dir,
            tile_extract="",
            verbose=False,
        )
        actor = Actor(config)

    if isinstance(origins, tuple):
        origins = [origins]

    if colours is None:
        default = [
            "#66c2a5",
            "#fc8d62",
            "#8da0cb",
            "#e78ac3",
            "#a6d854",
            "#ffd92f",
        ]
        colours = {c: default[i % len(default)] for i, c in enumerate(sorted(contours))}

    if origin_kwargs is None:
        origin_kwargs = dict(color="red", markersize=80)

    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 8))

    all_isochrones = []

    for origin in origins:
        request = {
            "locations": [
                {
                    "lat": origin[1],
                    "lon": origin[0],
                }
            ],
            "costing": mode,
            "contours": [{"time": c} for c in contours],
            "polygons": True,
            "denoise": 1.0,
            "generalize": 0,
        }

        geojson = actor.isochrone(request)

        iso = geopandas.GeoDataFrame.from_features(
            geojson["features"],
            crs="EPSG:4326",
        )

        iso["origin"] = str(origin)

        all_isochrones.append(iso)

    isochrones = geopandas.GeoDataFrame(
        pd.concat(all_isochrones, ignore_index=True),
        crs="EPSG:4326",
    )

    iso_web = isochrones.to_crs(3857)

    origin_web = geopandas.GeoDataFrame(
        geometry=[Point(xy) for xy in origins],
        crs="EPSG:4326",
    ).to_crs(3857)

    for contour in sorted(contours, reverse=True):
        group = iso_web[iso_web["contour"] == contour]

        if not group.empty:
            group.plot(
                ax=ax,
                color=colours[contour],
                alpha=alpha,
                edgecolor="black",
                linewidth=0.5,
                label=f"{contour} min",
            )

    origin_web.plot(ax=ax, label="Origin", **origin_kwargs)

    if add_basemap:
        cx.add_basemap(ax)

    handles, labels = ax.get_legend_handles_labels()

    # Remove duplicate legend entries
    unique = dict(zip(labels, handles))

    ordered_labels = [f"{c} min" for c in sorted(contours)] + ["Origin"]
    ordered_handles = [unique[l] for l in ordered_labels if l in unique]

    ax.legend(ordered_handles, ordered_labels, title="Travel time")

    ax.set_axis_off()

    if title is not None:
        ax.set_title(title)

    # return isochrones
