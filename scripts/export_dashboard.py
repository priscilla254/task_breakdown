"""Export a read-only Gantt dashboard (search + status filter + full screen)
for static hosting, e.g. GitHub Pages.

Reads data/tasks-*.json directly (no server needed). Read-only (no editing),
since there's no backend once it's published.

Usage:
    python scripts/export_dashboard.py                    # docs/index.html, phase1
    python scripts/export_dashboard.py --project training
    python scripts/export_dashboard.py --out docs          # choose output folder
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import PROJECTS
from services.dashboard_export import build_dashboard_html


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", default="phase1", choices=list(PROJECTS), help="Project id (default: phase1)")
    parser.add_argument("--out", default="docs", help="Output directory (default: docs/, GitHub Pages' default source folder)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    html = build_dashboard_html(args.project)

    index_path = os.path.join(args.out, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {index_path}")

    # Disable Jekyll processing so GitHub Pages serves the file as-is.
    nojekyll_path = os.path.join(args.out, ".nojekyll")
    open(nojekyll_path, "w").close()
    print(f"Wrote {nojekyll_path}")


if __name__ == "__main__":
    main()
