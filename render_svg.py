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

# You will almost definitely need to update this yourself
INKSCAPE = "/opt/local/bin/inkscape"

# Paths are relative to the location of this file, which must be
# in the project root

SOURCE_DIR = "Artwork"                  # default: "Artwork"
RENDER_DIR = "Renders"                  # default: "Renders"

AUTH_TAG_FILE = "ppau_auth_tag.txt"     # default: "ppau_auth_tag.txt"
PRINT_TAG_FILE = "ppau_print_tag.txt"   # default: "ppau_auth_tag.txt"

# The text below is found, and replaced with the content of the respective
# file listed above. Neither may be an SVG tag, for obvious reasons.

AUTH_TAG = "PPAU_AUTH_TAG"              # default: "PPAU_AUTH_TAG"
PRINT_TAG = "PPAU_PRINT_TAG"            # default: "PPAU_PRINT_TAG"


################################################################################
#### You shouldn't need to edit anything below this comment.                ####
################################################################################

import subprocess
import os
import sys
import shutil
import shlex
import tempfile
import time

# Insert defaults if left empty

if SOURCE_DIR == "":
    SOURCE_DIR == "." # *actual* default.
if RENDER_DIR == "":
    RENDER_DIR == "Renders"
if AUTH_TAG_FILE == "":
    AUTH_TAG_FILE = "ppau_auth_tag.txt"
if PRINT_TAG_FILE == "":
    PRINT_TAG_FILE = "ppau_print_tag.txt"
if AUTH_TAG == "":
    AUTH_TAG = "PPAU_AUTH_TAG"
if PRINT_TAG == "":
    PRINT_TAG = "PPAU_PRINT_TAG"

# Fix directory issues

pushd = os.getcwd()

if sys.path[0]:
    os.chdir(sys.path[0])

### Reset RENDER_DIR
##
##if os.path.isdir(RENDER_DIR):
##    print("RENDER_DIR exists.")
##    shutil.rmtree(RENDER_DIR)
##
##os.makedirs(RENDER_DIR)

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
        auth_tag_full = shlex.quote(atfp.read())
except FileNotFoundError:
    print("Authorisation tag file not found!",
          "No substitution will be performed.")
    auth_tag_full = shlex.quote(AUTH_TAG)

try:        
    with open(PRINT_TAG_FILE) as ptfp:
        print_tag_full = shlex.quote(ptfp.read())
except FileNotFoundError:
    print("Printing tag file not found!",
          "No substitution will be performed.")
    print_tag_full = shlex.quote(PRINT_TAG)
        
# Iterate over SVGs

for s in SVGs:
    if len(s) == 0:
        continue
    # print(s)    
    (sdir, sbase) = os.path.split(s)

    # We shall first output the auth'd SVGs to RENDERDIR

    rdir = os.path.join(RENDER_DIR, sdir.replace(SOURCE_DIR + os.path.sep, ""))
    (rsroot, rsext) = os.path.splitext(sbase)
    rs = os.path.join(rdir, rsroot + "-tagged" + rsext)    
    rspdf = os.path.join(rdir, rsroot) + ".pdf"

    # check file modification dates and skip if 'no change'

    if os.path.exists(rspdf):
        s_change = os.path.getmtime(s)
        r_change = os.path.getmtime(rspdf)

        if s_change < r_change: # SVG older than PDF
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

        # and finally invoke Inkscape for the PDF
        subprocess.run([INKSCAPE,
                        "-z",               # silence
                        "-f", tmpfp.name,    # input file
                        "-A", rspdf])       # export PDF to output file
        

# revert cwd

os.chdir(pushd)

# this would've been a makefile,
# but `make` really doesn't like filenames with spaces in them
    
