#!/usr/bin/env python3

################################################################################
#### ABOUT:                                                                 ####
#### Get unique fontnames out of the SVGs in the artwork directory.         ####
#### The names will be placed in a file.
################################################################################

SOURCE_DIR = "Artwork"                  # default: "Artwork"
OUTPUT_FILE = "FONTLIST.json"            # default: "FONTLIST.txt"

################################################################################
#### You shouldn't need to ever edit anything below this comment.           ####
################################################################################

VERSION = "0.0.1"

import subprocess
import argparse
import re
import json

# Parse Arguments

parser = argparse.ArgumentParser(description="Collate the fonts used.", prog="PPAU-Graphics Font Lister")

parser.add_argument('--source_dir', dest='source_dir',
                    action='store', default=SOURCE_DIR,
                    help="The directory containing the source files.")

parser.add_argument('--output_file', dest='output_file',
                    action='store', default=OUTPUT_FILE,
                    help="The file listing the fonts.")

parser.add_argument('--version', action='version', version='%(prog)s '+VERSION)

args = parser.parse_args()

# Update Flags

SOURCE_DIR = args.source_dir
OUTPUT_FILE = args.output_file

combo = {}

allnames = set([])

pattern = re.compile(r"font-family(:|=)['\"]?([^;>'\"]*)")

# Recursively find all SVGs in SOURCE_DIR
SVGs = subprocess.run(["find", SOURCE_DIR, "-type", "f", "-name", "*.svg"],
                       stdout=subprocess.PIPE,
                       universal_newlines=True)\
        .stdout.strip().split(sep="\n")


for s in SVGs:
    if len(s) == 0:
        continue

    results = set([])

    with open(s, 'r', encoding="utf-8") as s_file:

        for line in s_file:
            match = pattern.search(line)
            if match:
                stripped = match.group(2).strip().strip('"').strip("'").strip()
                if stripped:
                    results.add(stripped)
    if len(results):
        combo[s] = results

        for n in results:
            allnames.add(n)



with open(OUTPUT_FILE, 'w') as fontlist_file:
    # pretty print

    keys = sorted(combo.keys())

    allfonts = [{'all' : sorted(list(allnames))}]

    tree = [{i : list(combo[i])} for i in keys]

    print(json.dumps(allfonts + tree), file=fontlist_file)


