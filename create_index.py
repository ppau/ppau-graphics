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
SITE_ROOT = "."    # you might need to put something here
# a `.` or `./` for local testing, something more substantial for on-server
# such as `./ppau-graphics`

POSTER_REPLACE_TAG = "PPAU_POSTERS_HERE"
ONLINE_REPLACE_TAG = "PPAU_ONLINES_HERE"


CONVERT = "convert"
CONVERT_PATH = ""

preconvargs = []
convargs = ["-background", "white", "-flatten", "-resize", "x400", "-quality", "80"]
# ^^^ give it a white bg if needed, maintain aspect ratio but make it 400px high

VERBOSE = False
VERSION = 0.3

import json
import os.path
import sys
import subprocess
import re
import argparse


# Handle our very minimal set of CL Args

argparser = argparse.ArgumentParser(description="Generate a static index page from a template, with JPEGs for the thumbnails.")
argparser.add_argument('--manifest-file', default=MANIFEST_FILE, help="Path to the manifest JSON file")
argparser.add_argument('--template-file', default=TEMPLATE_FILE, help="Path to the template HTML file")
argparser.add_argument('--index-file', default=INDEX_FILE, help="Path to put the generated index HTML file")
argparser.add_argument('--render-dir', default=RENDER_DIR, help="Path to the render directory")
argparser.add_argument('--site-root', default=SITE_ROOT, help="Path for the root of the index page; default is `"+SITE_ROOT+"`")
argparser.add_argument('--poster-replace-tag', default=POSTER_REPLACE_TAG, help="The string in the template to be replaced by the poster content")
argparser.add_argument('--online-replace-tag', default=ONLINE_REPLACE_TAG, help="The string in the template to be replaced by the online-only content")
argparser.add_argument('--verbose', default=VERBOSE, action='store_true', help="Show ALL the debugging output!")
argparser.add_argument('--version', action='version', version=VERSION)

arguments = argparser.parse_args()

# Just a little helper function
def printv(*args, **kwargs):
    if arguments.verbose:
        print(*args, **kwargs, file=sys.stderr)

printv("Command line arguments:", arguments)

# make `convert` work (on posix systems)
if not os.path.exists(CONVERT_PATH):
    printv("`"+ CONVERT + "` not found at specified path `" + CONVERT_PATH + "`.")

    if os.name == "posix":
        converttry = subprocess.run(["which", CONVERT],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
        if converttry:
            printv("Using `"+ CONVERT +"` at `" + converttry + "` instead.")
            CONVERT_PATH = converttry
        else:
            print("ERROR: could not find `"+ CONVERT +"`!", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: could not find `"+ CONVERT +"`!", file=sys.stderr)
        sys.exit(1)



# General structure: we need to generate a sequence of
#   <div><img><p>caption</p></div>'s.


poster_replacement_str = ''
online_replacement_str = ''
src_str = ""
out_str = ""

printv("\ntitle", "count", "thumbnail path", sep="\t")

# Collate posters.
with open(arguments.manifest_file, 'r') as mani_fp:
    manifest = json.load(mani_fp)

    for m in manifest:
        k = list(m.keys())[0]

        onlineOnlyFlag = False

        if len(m[k]) == 6:
            pass
        elif len(m[k]) == 4:
            # do something interesting
            onlineOnlyFlag = True
        else:
            continue

        if m[k][0].startswith('_'):
            continue

        ourfile = m[k][1]
        r_in = os.path.join(arguments.render_dir, ourfile)
        r_out = os.path.join(arguments.render_dir, ourfile[0:-4] + "_preview" + "." + "jpg")

        dlname = os.path.splitext(os.path.basename(ourfile))[0][0:-5]

        printv(k, len(m[k]), r_in, r_out, ourfile, sep="\t") # [1] is *-auth.png

        flippy = subprocess.run([CONVERT_PATH] + preconvargs + [r_in]
                              + convargs
                              + [r_out],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        printv("stdout from ^^^:", flippy.stdout.decode())
        printv("stderr from ^^^:", flippy.stderr.decode())

        if not onlineOnlyFlag:
            poster_replacement_str += '      <hr>\r\n      <div>\r\n        '+\
            '<img src="'+arguments.site_root+'/'+r_out+'" alt="'+k+'">'+'\r\n        '+ \
            '<p class="caption"><a href="'+arguments.site_root+'/'+r_in+'" download="'+dlname+'">'+k+'</a></p>\r\n      </div>\r\n'
        else:
            online_replacement_str += '      <hr>\r\n      <div>\r\n        '+\
            '<img src="'+arguments.site_root+'/'+r_out+'" alt="'+k+'">'+'\r\n        '+ \
            '<p class="caption"><a href="'+arguments.site_root+'/'+r_in+'" download="'+dlname+'">'+k+'</a></p>\r\n      </div>\r\n'

# Close off the two `<div>`s


printv("\nPoster Replacement String:\n", poster_replacement_str)


with open(arguments.template_file) as templatefp:
    out_str = templatefp.read().replace(arguments.poster_replace_tag, poster_replacement_str)
    out_str = out_str.replace(arguments.online_replace_tag, online_replacement_str)


with open(arguments.index_file, 'w') as indexfp:
    print(out_str, file=indexfp)
