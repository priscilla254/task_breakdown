"""Export a project's Gantt chart as a self-contained interactive HTML file.

Reads data/tasks-*.json directly (no server needed). The output HTML embeds
plotly.js, so it opens in any browser with full interactivity (hover, zoom,
pan) even with no internet connection.

Usage:
    python scripts/export_html.py                  # export every project
    python scripts/export_html.py --project phase1  # export one project
    python scripts/export_html.py --out exports     # choose output folder
"""

import argparse
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_manager import PROJECTS
from services.export_service import tasks_to_html


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", choices=list(PROJECTS), help="Project id (default: all projects)")
    parser.add_argument("--out", default="exports", help="Output directory (default: exports/)")
    args = parser.parse_args()

    project_ids = [args.project] if args.project else list(PROJECTS)
    os.makedirs(args.out, exist_ok=True)

    for pid in project_ids:
        html = tasks_to_html(pid, embed_js=True)
        filename = f"{pid}-gantt-{date.today().isoformat()}.html"
        path = os.path.join(args.out, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
