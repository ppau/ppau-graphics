#!/usr/bin/env python3

################################################################################
#### ABOUT:                                                                 ####
#### Quick little script to generate a new static page for the WSGI         ####
#### Old approach dynamically loaded the full-size PNGs, which while nice   ####
####    to be able to just right-click and "Save As" was very slow to load. ####
################################################################################

MANIFEST_FILE = "MANIFEST.json"
TEMPLATE_FILE = "page_src.html"
INDEX_FILE = "index.html"

RENDER_DIR = "Renders"                  # default: "Renders"
SITE_ROOT = "./"    # you might need to put something here
# a `.` or `./` for local testing, something more substantial for on-server

REPLACE_TAG = "PPAU_ITEMS_HERE"

CONVERT = "convert"
CONVERT_PATH = ""

preconvargs = []
convargs = ["-background", "white", "-flatten", "-resize", "x400", "-quality", "80"]

VERBOSE = False

import json
import os.path
import sys
import subprocess
import re


# Just a little helper function
def printv(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs, file=sys.stderr)

# make `convert` work (on posix systems)
if not os.path.exists(CONVERT_PATH):
    printv(CONVERT + " not found at specified path " + CONVERT_PATH)

    if os.name == "posix":
        converttry = subprocess.run(["which", CONVERT],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
        if converttry:
            printv("Using "+ CONVERT +" at " + converttry + " instead.")
            CONVERT_PATH = converttry
        else:
            print("ERROR: could not find "+ CONVERT +"!", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: could not find "+ CONVERT +"!", file=sys.stderr)
        sys.exit(1)



# General structure: we need to generate a sequence of
#   <div><img><p>caption</p></div>'s.


replacement_str = ""
src_str = ""
out_str = ""

with open(MANIFEST_FILE, 'r') as mani_fp:
    manifest = json.load(mani_fp)

    for m in manifest:
        k = list(m.keys())[0]

        if len(m[k]) < 6:
            continue

        if m[k][0].startswith('_'):
            continue

        ourfile = m[k][1]

        r_in = os.path.join(RENDER_DIR, ourfile)
        r_out = os.path.join(RENDER_DIR, ourfile[0:-4] + "_preview" + "." + "jpg")


        printv(k, len(m[k]), r_out) # [1] is *-auth.png

        flippy = subprocess.run([CONVERT_PATH] + preconvargs + [r_in]
                              + convargs
                              + [r_out],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        printv(flippy.stdout.decode())
        printv(flippy.stderr.decode())

        replacement_str += '      <hr>\r\n      <div>\r\n        '+\
        '<img src="'+SITE_ROOT+'/'+r_out+'" alt="'+k+'">'+'\r\n        '+ \
        '<p class="caption"><a href="'+SITE_ROOT+'/'+r_in+'">'+k+'</a></p>\r\n      </div>\r\n'


printv(replacement_str)


with open(TEMPLATE_FILE) as templatefp:
    out_str = templatefp.read().replace(REPLACE_TAG, replacement_str)


with open(INDEX_FILE, 'w') as indexfp:
    print(out_str, file=indexfp)
