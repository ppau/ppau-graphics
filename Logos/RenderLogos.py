#! /usr/bin/python3

## A little script to render all the logos. ##

## Settings ##

BACKEND_PATH = "/usr/bin/inkscape"
BACKEND = "inkscape"

SOURCE_DIR = "."                        # default: "."
RENDER_DIR = "Renders"                  # default: "Renders"

VERBOSE = False

FORMATS = ["pdf", "png"]

VERSION = "0.1.0a"

TEMPLATE_FILE = "logo_src.html"
LOGOS_REPLACE_TAG = "PPAU_LOGOS_HERE"
INDEX_FILE = "index.html"
PAGE_ROOT = "."    # you might need to put something here
# a `./Logos` or `./Logos/` for local testing
# something more substantial for on-server
# such as `./ppau-graphics/Logos`

CONVERT = "convert"
CONVERT_PATH = ""

preconvargs = []
convargs = ["-background", "#fff", "-flatten", "-resize", "x400", "-quality", "80"]
# ^^^ give it a white bg if needed, maintain aspect ratio but make it 400px high


## Alrighty... ###

import sys
import os
import subprocess
import argparse

# eventual argparsing will go here

# Just a little helper function
def printv(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs, file=sys.stderr)

# Absolutise basepaths
if sys.path[0]:
    if not os.path.isabs(SOURCE_DIR):
        SOURCE_DIR = os.path.join(sys.path[0], SOURCE_DIR.rstrip("."))
    if not os.path.isabs(RENDER_DIR):
        RENDER_DIR = os.path.join(sys.path[0], RENDER_DIR.rstrip("."))

printv("Source Dir:", SOURCE_DIR, "Render Dir:", RENDER_DIR)

printv("Version:", VERSION)


# make BACKEND work (on posix systems)
if not os.path.exists(BACKEND_PATH):
    printv(BACKEND + " not found at specified path " + BACKEND_PATH)

    if os.name == "posix":
        backendtry = subprocess.run(["which", BACKEND],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
        if backendtry:
            printv("Using "+ BACKEND +" at " + backendtry + " instead.")
            BACKEND_PATH = backendtry
        else:
            print("ERROR: could not find "+ BACKEND +"!", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: could not find "+ BACKEND +"!", file=sys.stderr)
        sys.exit(1)


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



outputs = {} # We'll use this later

# Recursively find all SVGs in SOURCE_DIR
SVGs = subprocess.run(["find", SOURCE_DIR, "-type", "f", "-name", "*.svg"],
                       stdout=subprocess.PIPE,
                       universal_newlines=True)\
        .stdout.strip().split(sep="\n")

# Iterate over `SVGs`...

for s in SVGs:
    printv(s)
    if len(s) == 0:
        continue
    (sdir, sbase) = os.path.split(s)

    printv(sdir, sbase)

    # Figure out where we're rendering to


        

    subdir = sdir.replace(os.path.commonpath([sdir, SOURCE_DIR]), "")

    rdir = os.path.join(RENDER_DIR, subdir.lstrip(os.path.sep))

    printv("replace:", subdir, "rdir:", rdir)

    (r_tag_root, r_tag_ext) = os.path.splitext(sbase)

    if not os.path.exists(rdir):
            # print(rdir)
            os.makedirs(rdir)

    results = [] # one result for each format

    renderargs = []

    outputs[s] = []

    # Iterate over output formats...
    for ftype in FORMATS:
        # Pathname of output file
        r_out = os.path.join(rdir, r_tag_root)  + "." + ftype

        outputs[s].append(r_out)

        # Now check to see if output file is newer
        if os.path.exists(r_out):
            if os.path.getmtime(s) <= os.path.getmtime(r_out):
                printv("No change: skipping", r_out, sep="\t")
                continue
        # (else:)
        printv("Rendering", r_out, sep="\t")

        if ftype == "png":
            renderargs = ["--export-dpi=300", "-e", r_out]
        elif ftype == "pdf":
            renderargs = ["--export-dpi=300", "--export-text-to-path", "-A", r_out]

        # output ALL the things
        if len(renderargs): # this line is quite an important optimisation!
            inky = subprocess.run([BACKEND_PATH, "-z"]
                                  + renderargs
                                  + ["-f", s],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            printv(inky.stdout.decode())
            printv(inky.stderr.decode())        


# Now iterate over `outputs`
replString = ""

sk = lambda k: (os.path.dirname(k), os.path.basename(k))

for okey in sorted(outputs.keys(), key=sk):
    item = outputs[okey]

    printv(okey, item)

    printv("lambda test:", sk(okey))

    png = ""
    pdf = ""

    for i in item:
        if i.endswith(".png"):
            png = i #.replace(os.path.commonpath([i, RENDER_DIR]), "")
        elif i.endswith(".pdf"):
            pdf = i #.replace(os.path.commonpath([i, RENDER_DIR]), "")

    r_in = png
    r_out = r_in[0:-4] + "_preview" + ".jpg"

    dlname = os.path.splitext(os.path.basename(okey))[0]
    caption = dlname #os.path.split(okey)[-1]
    #printv("Possible captioning:", os.path.split(okey))

    # handle 'negative' images correctly
    if 'negative' in okey:
        convargs[1] = "black"
    else:
        convargs[1] = "white"

    # Now check to see if output file is newer
        if os.path.exists(r_out) and os.path.getmtime(r_in) <= os.path.getmtime(r_out):
                printv("No change: skipping", r_out, sep="\t")
        else:
            flippy = subprocess.run([CONVERT_PATH] + preconvargs + [r_in]
                                  + convargs
                                  + [r_out],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            printv("stdout from ^^^:", flippy.stdout.decode())
            printv("stderr from ^^^:", flippy.stderr.decode())

    pr_abs = os.path.abspath(PAGE_ROOT)

    r_out_html = r_out.replace(os.path.commonpath([r_out, pr_abs]), "")
    svg_html = okey.replace(os.path.commonpath([okey, pr_abs]), "")
    png_html = png.replace(os.path.commonpath([png, pr_abs]), "")
    pdf_html = pdf.replace(os.path.commonpath([pdf, pr_abs]), "")

    replString += '<div>\r\n\t'+\
                  '<img src="'+PAGE_ROOT+r_out_html+'" alt="'+dlname+'">\r\n\t'+\
                  '<p class="caption">'+dlname+'</p>\r\n\t'+\
                  '<p class="links">Download as:&nbsp;&nbsp;'+\
                  '<a href="'+PAGE_ROOT+svg_html+'">SVG</a>&nbsp;&nbsp;'+\
                  '<a href="'+PAGE_ROOT+pdf_html+'">PDF</a>&nbsp;&nbsp;'+\
                  '<a href="'+PAGE_ROOT+png_html+'">PNG</a>&nbsp;&nbsp;'+\
                  '</p>\r\n</div>\r\n'
    
printv("\nReplacement String:", replString)

out_str = ""
with open(TEMPLATE_FILE) as templatefp:
    out_str = templatefp.read().replace(LOGOS_REPLACE_TAG, replString)

with open(INDEX_FILE, 'w') as indexfp:
    print(out_str, file=indexfp)
