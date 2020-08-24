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

VERSION = "0.0.2"

import subprocess
import argparse
import re
import json
import sys

# Parse Arguments

parser = argparse.ArgumentParser(description="Collate the fonts used.", prog="PPAU-Graphics Font Lister")

parser.add_argument('--source_dir', dest='source_dir',
                    action='store', default=SOURCE_DIR,
                    help="The directory containing the source files.")

parser.add_argument('--output_file', dest='output_file',
                    action='store', default=OUTPUT_FILE,
                    help="The file listing the fonts.")

parser.add_argument('--list', dest='list_too',
                     action='store_const', default=False, const=True,
                     help="List all font names to standard output")

parser.add_argument('--show-missing', dest='show_missing',
                     action='store_const', default=False, const=True,
                     help="List all missing font names to standard output")

parser.add_argument('--version', action='version', version='%(prog)s '+VERSION)

arguments = parser.parse_args()

# Update Flags

SOURCE_DIR = arguments.source_dir
OUTPUT_FILE = arguments.output_file

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


listnames = sorted(list(allnames))

with open(arguments.output_file, 'w') as fontlist_file:
    # pretty print

    keys = sorted(combo.keys())

    allfonts = [{'all' : listnames}]

    tree = [{i : list(combo[i])} for i in keys]

    print(json.dumps(allfonts+tree), file=fontlist_file)
    
if arguments.list_too:
    print(*listnames, sep='\n')


if arguments.show_missing:
    installed_fonts = None

    fcl_try = subprocess.run(["which", "fc-list"],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
    
    
    if fcl_try:
        installed_fonts = set(subprocess.run([fcl_try, ':', 'family'],
                   stdout=subprocess.PIPE,
                   universal_newlines=True)\
        .stdout.strip().split(sep="\n"))
    elif sys.platform == 'darwin':
        installed_fonts = subprocess.run(['system_profiler', 'SPFontsDataType'],
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT,
           universal_newlines=True)\
        .stdout.strip()
    else:
        print("Could not list system fonts. (Windows is currently not supported.)")
        exit(1)
    
    for font in listnames:
        if font not in installed_fonts:
            print(font)


