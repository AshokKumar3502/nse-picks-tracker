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
    import json
    try:
        doc = json.load(open(a.source, encoding="utf-8"))
    except ValueError as e:
        print("NOT PUBLISHED: %s is not valid JSON (%s)" % (a.source, e))
        return 1
    built = next((m.get("value") for m in doc.get("meta") or [] if m.get("label") == "Built"), "")
    if not doc.get("rows"):
        print("NOT PUBLISHED: %s has no rows" % a.source)
        return 1
    import datetime
    age = (datetime.date.today() - datetime.date.fromisoformat(built[:10])).days if built[:10] else 99
    if age > 3:
        print("NOT PUBLISHED: the data was built %s, %d days ago: run india-tracker/track.py build first" % (built, age))
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
      try:
        root = os.path.dirname(os.path.dirname(os.path.dirname(a.source)))
        src = json.load(open(heat, encoding="utf-8")).get("html") or ""
        src = src if os.path.isabs(src) else os.path.join(root, src.replace("\\", os.sep))
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(HERE, "heatmap.html"))
        else:
            print("WARNING: the heatmap file %s is missing; the site keeps the old heatmap" % src)
      except (OSError, ValueError) as e:
        print("WARNING: heatmap not copied (%s); the site keeps the old heatmap" % e)
    note = os.path.join(os.path.dirname(a.source), "notify.json")
    if os.path.exists(note):            # phone notifications for the Android app
        shutil.copyfile(note, os.path.join(HERE, "data", "notify.json"))
    paths = ["data/picks.json", "data/indices.json", "data/charts", "heatmap.html"]
    if os.path.exists(os.path.join(HERE, "data", "notify.json")):
        paths.append("data/notify.json")
    r = git("add", *paths)
    if r.returncode:
        print("NOT PUBLISHED: git add failed: " + (r.stderr or r.stdout))
        return 1
    if not git("diff", "--cached", "--quiet").returncode:
        print("No change in the data: nothing to publish.")
        return 0
    r = git("commit", "-m", "Update picks data")
    if r.returncode:
        print(r.stdout + r.stderr)
        return 1
    for attempt in range(3):           # the cloud engine and this laptop may both publish: take theirs first
        pull = git("pull", "--rebase", "-X", "theirs", "origin", "main")
        if pull.returncode:
            git("rebase", "--abort")
            print("WARNING: pull before push failed: " + (pull.stderr or pull.stdout).strip()[:200])
        r = git("push", "origin", "HEAD")
        if not r.returncode:
            break
    print(r.stdout + r.stderr)
    if r.returncode:
        return 1
    print("Published. The site updates within a minute or two.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
