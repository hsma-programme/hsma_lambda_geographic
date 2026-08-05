import matplotlib.pyplot as plt
import geopandas
from pyproj import Geod
import contextily as cx
from shapely.geometry import Point, LineString
from valhalla import Actor, get_config
import pandas as pd
import folium
from folium.plugins import Fullscreen, LocateControl, MarkerCluster, MiniMap
from IPython.display import HTML
import numpy as np


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


def fancy_point_map(
    problem_simplest, height=450
):  # Defaulted to 450 to prevent slide overflow
    # 1. Data Preparation
    np.random.seed(42)
    gdf = problem_simplest.candidate_sites.copy().to_crs("EPSG:4326")
    n_sites = len(gdf)

    gdf["Beds"] = np.random.randint(15, 650, n_sites)
    gdf["Annual Attendances"] = np.random.randint(3000, 120000, n_sites)
    gdf["Travel Catchment"] = np.random.randint(12000, 180000, n_sites)
    gdf["Average Rating"] = np.round(np.random.uniform(3.8, 4.9, n_sites), 1)

    # Color mapping matching hospital type
    TYPE_COLORS = {
        "Acute Hospital": "#e53935",  # Vibrant Red
        "Community Hospital": "#43a047",  # Vibrant Green
        "Minor Injury Unit": "#1e88e5",  # Vibrant Blue
    }

    # 2. Map Initialization using folium.Figure to explicitly control height
    fig = folium.Figure(height=height)
    m = folium.Map(
        location=[50.75, -3.75], zoom_start=9, tiles="CartoDB Positron"
    ).add_to(fig)

    # Marker Cluster Group
    cluster = MarkerCluster(
        name="Clustered Facilities",
        overlay=True,
        control=True,
        show=False,
        icon_create_function="""
        function(cluster) {
            var count = cluster.getChildCount();
            return L.divIcon({
                html: '<div style="background-color:rgba(21, 101, 192, 0.85); color:white; border-radius:50%; width:36px; height:36px; display:flex; align-items:center; justify-content:center; font-weight:bold; border:2px solid white; box-shadow:0 0 8px rgba(0,0,0,0.4);">' + count + '</div>',
                className: 'marker-cluster-custom',
                iconSize: L.point(36, 36)
            });
        }
        """,
    ).add_to(m)

    # Separate Feature Group for Sized Volume Points
    volume_group = folium.FeatureGroup(
        name="Volume Sized Points (Attendances)", show=True
    ).add_to(m)

    # Calculate min/max for dynamic marker radius scaling
    min_att = gdf["Annual Attendances"].min()
    max_att = gdf["Annual Attendances"].max()

    # 3. Add Clustered Pins & Sized Volume Points
    for _, row in gdf.iterrows():
        color = TYPE_COLORS.get(row.Type, "#757575")

        popup_html = f"""
        <div style="width:280px">
            <h3 style="margin-bottom:5px;color:#1565c0;">🏥 {row.Facility_Name}</h3>
            <table style="width:100%;font-size:13px">
                <tr><td><b>Type</b></td><td>{row.Type}</td></tr>
                <tr><td><b>Beds</b></td><td>{row.Beds}</td></tr>
                <tr><td><b>Annual attendances</b></td><td>{row["Annual Attendances"]:,}</td></tr>
                <tr><td><b>Catchment</b></td><td>{row["Travel Catchment"]:,}</td></tr>
                <tr><td><b>Patient rating</b></td><td>⭐ {row["Average Rating"]}</td></tr>
            </table>
            <hr>
            <i>Click to explore travel times and accessibility.</i>
        </div>
        """

        tooltip_html = f"""
        <div style="
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding: 6px 10px;
            min-width: 180px;
            color: #212121;
        ">
            <div style="font-size: 14px; font-weight: 700; margin-bottom: 4px; color: #0d47a1;">
                🏥 {row.Facility_Name}
            </div>

            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                <span style="
                    background-color: {color};
                    color: white;
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                    border-radius: 4px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                ">
                    {row.Type}
                </span>
                <span style="font-size: 11px; font-weight: 600; color: #f57c00;">
                    ⭐ {row["Average Rating"]}
                </span>
            </div>

            <div style="
                border-top: 1px solid #e0e0e0;
                padding-top: 4px;
                font-size: 11px;
                color: #616161;
                display: flex;
                justify-content: space-between;
            ">
                <span>Annual Volume:</span>
                <b style="color: #212121;">{row["Annual Attendances"]:,}</b>
            </div>
        </div>
        """

        # A) Standard Pin Inside Cluster
        folium.Marker(
            [row.geometry.y, row.geometry.x],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=tooltip_html,
            icon=folium.Icon(
                color="blue"
                if color == "#1e88e5"
                else ("red" if color == "#e53935" else "green"),
                icon="hospital-o",
                prefix="fa",
            ),
        ).add_to(cluster)

        # B) Proportional Sized Circle (Radius scales between 6px and 24px)
        radius_px = 6 + 18 * (
            (row["Annual Attendances"] - min_att) / (max_att - min_att + 1e-5)
        )

        # Add the styled tooltip to your markers
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=radius_px,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(volume_group)

    # 4. Floating Legend Overlay (Reverted to fixed so it pins to the internal iframe)
    legend_html = """
    <div style="
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 200px;
        background: rgba(255, 255, 255, 0.95);
        z-index: 9999;
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 0 10px rgba(0,0,0,0.2);
        font-family: sans-serif;
        font-size: 12px;
        pointer-events: none;
    ">
        <b>Hospital Type</b><br><br>
        🔴 Acute Hospital<br>
        🟢 Community Hospital<br>
        🔵 Minor Injury Unit
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # 5. Controls & Plugins
    MiniMap(toggle_display=True, position="bottomright", zoom_level_offset=-5).add_to(m)

    Fullscreen(
        position="topright", title="Expand map", title_cancel="Exit fullscreen"
    ).add_to(m)

    LocateControl().add_to(m)

    folium.TileLayer("CartoDB Positron", name="Light Canvas (Default)").add_to(m)
    folium.TileLayer("CartoDB Voyager", name="Detailed Navigation").add_to(m)
    folium.TileLayer("CartoDB Dark_Matter", name="Dark Mode (High Contrast)").add_to(m)
    folium.TileLayer("OpenStreetMap", name="Street Level (OSM)").add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Returning the Figure object renders perfectly natively in Quarto
    return fig
