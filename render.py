################################################################################
#### ABOUT:                                                                 ####
#### Render script for the SVGs in the SOURCE_DIR directory.                ####
#### The renders will be placed in RENDER_DIR. 			            ####
#### If possible, SVGs containing AUTH_TAG or PRINT_TAG will have           ####
#### the full tags inserted.                                                ####
####                                                                        ####
#### CAVEATS:                                                               ####
#### While spaces in filenames are supported, newlines are not.             ####
#### Presently, authorisation and printing tags will be inserted wholly     ####
#### on one line. No flowed text.                                           ####
################################################################################

#### You can override these defaults at run-time via command-line flags.    ####

# You will almost definitely need to update this yourself
RSVG_PATH = "/opt/local/bin/rsvg-convert"

# If the paths below are relative, this file is assumed to be in the
# project's root directory.

SOURCE_DIR = "Artwork"                  # default: "Artwork"
RENDER_DIR = "Renders"                  # default: "Renders"

AUTH_TAG_FILE = "ppau_auth_tag.txt"     # default: "ppau_auth_tag.txt"
PRINT_TAG_FILE = "ppau_print_tag.txt"   # default: "ppau_auth_tag.txt"

# The text below is found, and replaced with the content of the respective
# file listed above. Neither may be an SVG tag, for obvious reasons.

AUTH_TAG = "PPAU_AUTH_TAG"              # default: "PPAU_AUTH_TAG"
PRINT_TAG = "PPAU_PRINT_TAG"            # default: "PPAU_PRINT_TAG"

#### Other defaults                                                         ####

FORMAT = "pdf"
VERBOSE = False

################################################################################
#### You shouldn't need to ever edit anything below this comment.           ####
################################################################################

# import all the things
import subprocess
import os
import sys
import shutil
import shlex
import tempfile
import time
import argparse

# Parse arguments

parser = argparse.ArgumentParser(description="Render the source files.")

parser.add_argument('--source_dir', dest='source_dir',
                    action='store', default=SOURCE_DIR,
                    help="The directory containing the source files.")

parser.add_argument('--render_dir', dest='render_dir',
                    action='store', default=RENDER_DIR,
                    help="Where to put the rendered files. " +
                        "It will be created if necessary.")
                   
parser.add_argument('--auth_tag_file', dest='auth_tag_file',
                    action='store', default=AUTH_TAG_FILE,
                    help="The file containing the authorisation text.")

parser.add_argument('--print_tag_file', dest='print_tag_file',
                    action='store', default=PRINT_TAG_FILE,
                    help="The file containing the printer location text.")

parser.add_argument('--auth_tag', dest='auth_tag',
                    action='store', default=AUTH_TAG,
                    help="The placeholder authorisation text.")

parser.add_argument('--print_tag', dest='print_tag',
                    action='store', default=PRINT_TAG,
                    help="The placeholder printer text.")

parser.add_argument('--backend_path', dest='rsvg_path',
                    action='store', default=RSVG_PATH,
                    help="The path to the backend renderer, " +
                            "usually your `rsvg-convert` install.")

parser.add_argument('--output_format', dest='output',
                    action='store', default='pdf',
                    choices=['png', 'pdf', 'ps', 'svg', 'xml', 'recording'],
                    help="Choose a file format for the render.")

parser.add_argument('--verbose', dest='verbose',
                    action='store_const', default=VERBOSE, const=True)

args = parser.parse_args()


# Update Flags

SOURCE_DIR == args.source_dir
RENDER_DIR == args.render_dir
AUTH_TAG_FILE = args.auth_tag_file
PRINT_TAG_FILE = args.print_tag_file
AUTH_TAG = args.auth_tag
PRINT_TAG = args.print_tag
RSVG = args.rsvg_path
OUTPUT = args.output
VERBOSE = args.verbose


# Fix directory issues by using absolute pathnames (if possible).
# (These come about because the current working directory is not
#   necessarily the project root directory).

if sys.path[0]:

    if not os.path.isabs(SOURCE_DIR):
        SOURCE_DIR = os.path.join(sys.path[0], SOURCE_DIR)

    if not os.path.isabs(RENDER_DIR):
        RENDER_DIR = os.path.join(sys.path[0], RENDER_DIR)

    if not os.path.isabs(AUTH_TAG_FILE):
        AUTH_TAG_FILE = os.path.join(sys.path[0], AUTH_TAG_FILE)

    if not os.path.isabs(PRINT_TAG_FILE):
        PRINT_TAG_FILE = os.path.join(sys.path[0], PRINT_TAG_FILE)

# Just a little helper function
def printv(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


# Recursively find all SVGs
SVGs = subprocess.run(["find", SOURCE_DIR, "-type", "f", "-name", "*.svg"],
                       stdout=subprocess.PIPE,
                       universal_newlines=True) \
       .stdout.strip().split(sep="\n")


# Load printing tags

auth_tag_full = ""    
print_tag_full = ""

try:
    with open(AUTH_TAG_FILE) as atfp:
        auth_tag_full = atfp.read()
        printv(auth_tag_full)
except FileNotFoundError:
    print("Authorisation tag file not found!",
          "No substitution will be performed.")
    auth_tag_full = AUTH_TAG

try:        
    with open(PRINT_TAG_FILE) as ptfp:
        print_tag_full = ptfp.read()
        printv(print_tag_full)
except FileNotFoundError:
    print("Printing tag file not found!",
          "No substitution will be performed.")
    print_tag_full = PRINT_TAG

        
# Iterate over SVGs

for s in SVGs:
    if len(s) == 0:
        continue
    printv(s)    
    (sdir, sbase) = os.path.split(s)

    # We shall first output the auth'd SVGs to RENDERDIR

    rdir = os.path.join(RENDER_DIR, sdir.replace(SOURCE_DIR + os.path.sep, ""))
    (rsroot, rsext) = os.path.splitext(sbase)
    rs = os.path.join(rdir, rsroot + "-tagged" + rsext)    
    rspdf = os.path.join(rdir, rsroot) + "." + OUTPUT

    # Check file modification dates and skip if 'no change':
    # tagged SVG and output file both already exist, with
    # the tagged SVG being older than the output file.

    if os.path.exists(rspdf) and os.path.exists(rs):
        rs_change = os.path.getmtime(rs)
        rspdf_change = os.path.getmtime(rspdf)

        if rs_change < rspdf_change:
            printv("Skipping", rspdf)
            continue
    
    # create file and run sed into it for the auth

    if not os.path.exists(rdir):
        # print(rdir)
        os.makedirs(rdir)

    with open(rs, "w") as tmpfp:
        subprocess.run(["sed",
                        "-e", "s/"+AUTH_TAG+"/"+auth_tag_full+"/",
                        "-e", "s/"+PRINT_TAG+"/"+print_tag_full+"/",
                        s],
                       stdout=tmpfp)
        
        # Invoke rsvg-convert for the PDF
        subprocess.run([RSVG_PATH,
                       "-f", OUTPUT,            # export as OUTPUT format
                        "-o", rspdf,            # to this filename
                        tmpfp.name])            # from this file
        

# this would've been a makefile,
# but `make` really doesn't like filenames with spaces in them
    
