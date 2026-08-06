"""Post-render cleanup: Quarto's default project type mirrors the whole
project directory into output-dir, not just the rendered deck. Delete
everything under docs/ except what the published site actually needs.
"""
import shutil
from pathlib import Path

DOCS = Path(__file__).parent / "docs"

KEEP = {
    "index.html",
    "slides_files",
    "_extensions",
    "assets",
    "code_examples",
    "fullscreen",
    "resources",
    "custom.scss",
    "_brand.yml",
    ".nojekyll",
    "_freeze",
}

if DOCS.is_dir():
    for entry in DOCS.iterdir():
        if entry.name in KEEP:
            continue
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()
        print(f"removed stray docs/{entry.name}")
