#!/usr/bin/env python3
"""Copy the tracker's latest picks.json into this site and push it to GitHub Pages.

    python publish.py                      # from this folder
    python publish.py --source PATH        # another picks.json

Only data/picks.json, data/indices.json, data/charts/ and heatmap.html are changed. Nothing is pushed when the data has not changed.
"""
import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "india-day-trader-skill", "trader-in", "tracker", "picks.json")


def git(*args):
    return subprocess.run(["git", "-C", HERE] + list(args), capture_output=True, text=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", default=DEFAULT)
    a = p.parse_args()
    if not os.path.exists(a.source):
        print("no %s: run india-tracker/track.py build first" % a.source)
        return 1
    dst = os.path.join(HERE, "data", "picks.json")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(a.source, dst)
    idx = os.path.join(os.path.dirname(a.source), "indices.json")
    if os.path.exists(idx):
        shutil.copyfile(idx, os.path.join(HERE, "data", "indices.json"))
    charts = os.path.join(os.path.dirname(a.source), "charts")
    if os.path.isdir(charts):
        out = os.path.join(HERE, "data", "charts")
        os.makedirs(out, exist_ok=True)
        for name in os.listdir(charts):
            if name.endswith(".json"):
                shutil.copyfile(os.path.join(charts, name), os.path.join(out, name))
    heat = os.path.join(os.path.dirname(os.path.dirname(a.source)), "heatmap", "latest.json")
    if os.path.exists(heat):           # the evening heatmap, as heatmap.html on the site
        import json
        root = os.path.dirname(os.path.dirname(os.path.dirname(a.source)))
        src = json.load(open(heat, encoding="utf-8")).get("html") or ""
        src = src if os.path.isabs(src) else os.path.join(root, src.replace("\\", os.sep))
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(HERE, "heatmap.html"))
    git("add", "data/picks.json", "data/indices.json", "data/charts", "heatmap.html")
    if not git("diff", "--cached", "--quiet").returncode:
        print("No change in the data: nothing to publish.")
        return 0
    r = git("commit", "-m", "Update picks data")
    if r.returncode:
        print(r.stdout + r.stderr)
        return 1
    r = git("push", "origin", "HEAD")
    print(r.stdout + r.stderr)
    if r.returncode:
        return 1
    print("Published. The site updates within a minute or two.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
