"""Export a read-only dashboard (Gantt + searchable/filterable task table,
tab-switchable between projects) for static hosting, e.g. GitHub Pages.

Reads data/tasks-*.json directly (no server needed). Unlike export_html.py
(one static chart per project, no filters), this produces a single page with
both projects, tabs, search, and the same filters as the live app — but is
read-only (no editing), since there's no backend once it's published.

Usage:
    python scripts/export_dashboard.py                # docs/index.html, all projects
    python scripts/export_dashboard.py --out docs      # choose output folder
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.dashboard_export import build_dashboard_html


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default="docs", help="Output directory (default: docs/, GitHub Pages' default source folder)")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    html = build_dashboard_html()

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
