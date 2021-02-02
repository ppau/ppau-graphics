#! /usr/bin/python3

## A little script to render all the logos. ##

## Settings ##

BACKEND_PATHS = ["/Applications/Inkscape.app/Contents/Resources/bin/inkscape", "/Applications/Inkscape.app/Contents/MacOS/inkscape", "/usr/bin/inkscape"]
BACKEND_PATH = "/usr/bin/inkscape"
BACKEND = "inkscape"

SOURCE_DIR = "."                        # default: "."
RENDER_DIR = "Renders"                  # default: "Renders"

VERBOSE = False

FORMATS = ["pdf", "png"]

VERSION = "0.2.2"

TEMPLATE_FILE = "logo_src.html"
LOGOS_REPLACE_TAG = "PPAU_LOGOS_HERE"
INDEX_FILE = "index.html"

PAGE_ROOT = "."
# On-server, set --page-root "https://example.tld/ppau-graphics/Logos"

CONVERT = "convert"
CONVERT_PATH = ""

preconvargs = []
convargs = ["-background", "#fff", "-flatten", "-resize", "282^>", "-quality", "80"]
# ^^^ give it a white bg if needed, then maintaining aspect ratio, scale so that 
# .... the *smaller* side is reduced to 282px (A-series ratio will have the larger be 400)


## Alrighty... ###

import sys
import os
import subprocess
import argparse
import datetime
import logging

# argparsing goes here
argparser = argparse.ArgumentParser(description="Generate a static index page from a template, with JPEGs for the thumbnails.")
argparser.add_argument('--page-root', default=PAGE_ROOT, help="Path for the root of the index page; default is `"+PAGE_ROOT+"`")
argparser.add_argument('--verbose', action='count', help="tell me more", default=0)
argparser.add_argument('--quiet', action='count', help="tell me less", default=0)
argparser.add_argument('--log', type=argparse.FileType('a'), default=sys.stderr, help="file to log to (default: stderr)")

arguments = argparser.parse_args()

__loglevel = logging.INFO
if arguments.quiet > arguments.verbose:
    __loglevel = logging.WARNING
elif arguments.quiet < arguments.verbose:
    __loglevel = logging.DEBUG

logging.basicConfig(stream=arguments.log, level=__loglevel, 
    format= "%(levelname)s: %(message)s" if arguments.log.name == "<stderr>" else "%(asctime)s %(levelname)s: %(message)s")

def printv(*args, sep=' ', **kwargs):
    logging.debug(sep.join([str(x) for x in args]), **kwargs)

def printq(*args, sep=' ', **kwargs):
    logging.info(sep.join([str(x) for x in args]), **kwargs)

def failure(*args, sep=' ', code=1, **kwargs):
    logging.info(sep.join([str(x) for x in args]), **kwargs)
    sys.exit(code)

PAGE_ROOT = arguments.page_root



# Absolutise basepaths
if sys.path[0]:
    if not os.path.isabs(SOURCE_DIR):
        SOURCE_DIR = os.path.join(sys.path[0], SOURCE_DIR.rstrip("."))
    if not os.path.isabs(RENDER_DIR):
        RENDER_DIR = os.path.join(sys.path[0], RENDER_DIR.rstrip("."))

printv("Source Dir:", SOURCE_DIR, "Render Dir:", RENDER_DIR)

printv("Version:", VERSION)



# make BACKEND work (on posix systems, anyway)
for bp in BACKEND_PATHS:
    if os.path.exists(bp):
        BACKEND_PATH = bp
        break
else:
    if os.name == "posix":
        backendtry = subprocess.run(["which", BACKEND],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
        if backendtry:
            printv("Using "+ BACKEND +" at " + backendtry + " instead.")
            BACKEND_PATH = backendtry
        else:
            failure("ERROR: could not find "+ BACKEND +"!")
    else:
        failure("ERROR: could not find "+ BACKEND +"!")

# Establish Inkscape version
inkv = "1.0"
if 'inkscape' in BACKEND_PATH:
    vtext = subprocess.run([BACKEND_PATH, "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    if b"Inkscape 0.9" in vtext:
        inkv = "0.9"
    elif b"Inkscape 1." in vtext:
	    pass
    else:
        failure("Unknown Inkscape version!")



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
            failure("ERROR: could not find `"+ CONVERT +"`!")
    else:
        failure("ERROR: could not find `"+ CONVERT +"`!")



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

        if inkv == "0.9":
            if ftype == "png":
                renderargs = ["-z", "--export-dpi=300", "-e", r_out, "-f"]
            elif ftype == "pdf":
                renderargs = ["-z", "--export-dpi=300", "--export-text-to-path", "-A", r_out, "-f"]
        elif inkv == "1.0":
            if ftype == "png":
                renderargs = ["--export-dpi=300", "--export-type=png", "-o", r_out]
            elif ftype == "pdf":
                renderargs = ["--export-dpi=300", "--export-text-to-path", "--export-type=pdf", "-o", r_out]


        # output ALL the things
        if len(renderargs): # this line is quite an important optimisation!
            inky = subprocess.run([BACKEND_PATH]
                                  + renderargs + [s],
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

    #printv("lambda test:", sk(okey))

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
    caption = os.path.splitext(okey.replace(os.path.commonpath([okey, SOURCE_DIR]), "").lstrip('/'))[0]

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
                  '<p class="caption">'+caption+'</p>\r\n\t'+\
                  '<p class="links">Download as:&nbsp;&nbsp;'+\
                  '<a href="'+PAGE_ROOT+svg_html+'">SVG</a>&nbsp;&nbsp;'+\
                  '<a href="'+PAGE_ROOT+pdf_html+'">PDF</a>&nbsp;&nbsp;'+\
                  '<a href="'+PAGE_ROOT+png_html+'">PNG</a>&nbsp;&nbsp;'+\
                  '</p>\r\n</div>\r\n'
    
# printv("\nReplacement String:", replString)

out_str = ""
with open(TEMPLATE_FILE) as templatefp:
    out_str = templatefp.read().replace(LOGOS_REPLACE_TAG, replString)

# metadata
out_str = out_str.replace("META_TIMESTAMP", datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z")

gitty = subprocess.run(["git", "describe", "--always"], stdout=subprocess.PIPE)
hashy = gitty.stdout.decode().strip()
out_str = out_str.replace("GIT_HASH", hashy)


with open(INDEX_FILE, 'w') as indexfp:
    print(out_str, file=indexfp)
