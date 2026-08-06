# Anybody Have a Map? — Geographic OR/DS for NHS Leaders

Slides and materials for a workshop on geographic operational research and data science,
part of the [Health Service Modelling Associates (HSMA)](https://hsma.co.uk) programme.

The audience is mid-to-senior NHS leaders with little or no data science/OR background,
often in organisations with immature (or no) data science/OR capacity.

The goal isn't to teach them to do this work themselves — it's to give them enough grounding to commission geographic OR/DS projects and critically interpret what comes back.

Two related standalone HSMA workshops cover discrete event simulation and machine learning for operational improvement in more depth.

## Format

Slides are built with [Quarto](https://quarto.org/) (revealjs), source in `slides.qmd`,
which stitches together the `_*.qmd` section files in order. Output renders to `docs/`
for GitHub Pages hosting.

The centrepiece is an interactive exercise: attendees work through a Streamlit "game"
(hosted separately at `C:/geographic_or_ds_playground`) where they pick a handful of
analyses from a pool of options and naively choose a "best" site after each, then face
the fact that different reasonable analyses point at different answers — setting up the
case for location optimisation.

## Rendering

```
quarto render
```

Output goes to `docs/index.html`. GitHub Pages is pointed at the `docs/` folder.

Python dependencies (routing/OSM tooling used by some slide examples, plus Jupyter/lint
tooling) are managed via `pyproject.toml`.

## Before delivery

**[final-things-to-check.md](final-things-to-check.md)** is the standing pre-delivery
checklist. Several slides hard-code figures (candidate site counts, combination counts,
number of optimiser measures, briefing budget) that actually live in the companion
Streamlit app's code and data. If you change the app, its data, or its scoring metrics,
check that file and update the affected slides before running the workshop.

## Notes

After editing `custom.scss`, close any open Quarto preview windows/terminals and restart
the preview from scratch — style changes don't reliably hot-reload.

### Installed extensions

- [quarto-stlite](https://github.com/whitphx/quarto-stlite) — embed interactive Streamlit apps
- [quarto-verticator](https://github.com/Martinomagnifico/quarto-verticator) — navigation for vertical slide stacks
- [reveal-header](https://github.com/shafayetShafee/reveal-header) — slide headers

### Useful shortcuts (presenting)

- `q` — toggle mouse to/from laser pointer
- `f` — fullscreen
- `s` — speaker view
- `Alt` + click — zoom in on a point; `Alt` + click again to reset

## Licence

Code is MIT-licensed; all other content (slides, text, images) is
[CC BY-NC-SA 4.0](http://creativecommons.org/licenses/by-nc-sa/4.0/). See
[LICENCE.md](LICENCE.md).
