#!/usr/bin/env python3

################################################################################
#### ABOUT:                                                                 ####
#### Render script for the SVGs in the SOURCE_DIR directory.                ####
#### The renders will be placed in RENDER_DIR.                         ####
#### If possible, SVGs containing AUTH_TAG or PRINT_TAG will have           ####
#### the full tags inserted.                                                ####
####                                                                        ####
#### CAVEATS:                                                               ####
#### While spaces in filenames are supported, newlines are not.             ####
#### Presently, authorisation and printing tags will be inserted wholly     ####
#### on one line. No flowed text.                                           ####
################################################################################

#### You can override these defaults at run-time via command-line flags.    ####

# You will almost definitely want to update this yourself
BACKEND_PATH = "/Applications/Inkscape.app/Contents/Resources/bin/inkscape"
# "/usr/bin/inkscape"
COLLATER_PATH = "/usr/bin/pdfunite"

# If the paths below are relative, this file is assumed to be in the
# project's root directory.

SOURCE_DIR = "Artwork"                  # default: "Artwork"
RENDER_DIR = "Renders"                  # default: "Renders"

AUTH_TAG_FILE = "auth_tag.txt"          # default: "ppau_auth_tag.txt"
PRINT_TAG_FILE = "print_tag.txt"        # default: "ppau_auth_tag.txt"

# The text below is found, and replaced with the content of the respective
# file listed above. Neither may be an SVG tag, for obvious reasons.

AUTH_TAG = "PPAU_AUTH_TAG"              # default: "PPAU_AUTH_TAG"
PRINT_TAG = "PPAU_PRINT_TAG"            # default: "PPAU_PRINT_TAG"

#### Other settings                                                         ####

VERBOSE = False

NO_COLLATE = False
COLLATE_FMT = r'(.*)(_[pP])(\d+)(-\w*)?$'
# Collation format regex spec: four groups, consisting of...
# 1. the primary file name,
# 2. an underscore and a P,
# 3. digit[s] specifying the page order
# 4. optional alphanumeric description starting with a hyphen
# [the extension follows and is handled separately]
# example: `relative/path/to/filename_p1.svg`

#### You can't currently override these at run-time                         ####

FORMATS = ["pdf", "png"]

        #   (name, include auth tag, include print tag)
VARIANTS = [("auth", True, False),
            ("both", True, True),
            ("none", False, False)]
        # NB: it's absurd to include a print tag but not an auth tag.

# Manifest output file

MANIFEST_FILE = "MANIFEST.json"

################################################################################
#### End users shouldn't need to ever edit anything below this comment.     ####
################################################################################

VERSION = "0.4.0a"

BACKEND = "inkscape"
COLLATER = "pdfunite"

# import all the things
import subprocess
import os
import sys
import shutil
import shlex
import tempfile
import time
import argparse
import filecmp
import json
import re

# Parse arguments

parser = argparse.ArgumentParser(description="Render the source files.", prog="PPAU-Graphics Renderscript")

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

parser.add_argument('--backend_path', dest='backend_path',
                    action='store', default=BACKEND_PATH,
                    help="The path to the backend renderer, " +
                            "by default your "+ BACKEND + " install.")

parser.add_argument('--no-collate', dest='no_collate',
                    action='store_const', default=NO_COLLATE, const=True,
                    help="Don't collate multi-page files.")

parser.add_argument('--collate-fmt', dest='collate_fmt',
                    action='store', default=COLLATE_FMT,
                    help="A regex string that matches your filename numbering pattern.")

parser.add_argument('--verbose', dest='verbose',
                    action='store_const', default=VERBOSE, const=True,
                    help="Be more verbose about file processing.")

parser.add_argument('--version', action='version', version='%(prog)s '+VERSION)

args = parser.parse_args()


# Update Flags

SOURCE_DIR = args.source_dir
RENDER_DIR = args.render_dir
AUTH_TAG_FILE = args.auth_tag_file
PRINT_TAG_FILE = args.print_tag_file
AUTH_TAG = args.auth_tag
PRINT_TAG = args.print_tag
BACKEND_PATH = args.backend_path
NO_COLLATE = args.no_collate
COLLATE_FMT = args.collate_fmt
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
        print(*args, **kwargs, file=sys.stderr)

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

# Go find COLLATER if we haven't already
if not os.path.exists(COLLATER_PATH) and not NO_COLLATE:
    printv("{} not found at specified path {}".format(COLLATER, COLLATER_PATH))

    if os.name == "posix":
        collatertry = subprocess.run(["which", COLLATER],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
        if backendtry:
            printv("Using "+ COLLATER +" at " + collatertry + " instead.")
            COLLATER_PATH = collatertry
        else:
            print("ERROR: could not find "+ COLLATER +"!", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: could not find "+ COLLATER +"!", file=sys.stderr)
        sys.exit(1)

# Recursively find all SVGs in SOURCE_DIR
SVGs = subprocess.run(["find", SOURCE_DIR, "-type", "f", "-name", "*.svg"],
                       stdout=subprocess.PIPE,
                       universal_newlines=True)\
        .stdout.strip().split(sep="\n")

# Load authorisation and printing tags

auth_tag_full = ""
print_tag_full = ""

try:
    with open(AUTH_TAG_FILE) as atfp:
        auth_tag_full = atfp.read().strip()
        printv(auth_tag_full)
except FileNotFoundError:
    print("Authorisation tag file not found!",
          "No substitution will be performed.")
    auth_tag_full = AUTH_TAG
try:
    with open(PRINT_TAG_FILE) as ptfp:
        print_tag_full = ptfp.read().strip()
        printv(print_tag_full)
except FileNotFoundError:
    print("Printing tag file not found!",
          "No substitution will be performed.")
    print_tag_full = PRINT_TAG


# We also want to keep a manifest of what we've done.
# {file basename, [paths to renders...]}
# but we don't actually want absolute pathnames for that
# we want them relative to the Source and Render dirs
manifest = {}

multipagers = {}

skipcount = 0
updatecount = 0
notagcount = 0

# Iterate over SVGs...

for s in SVGs:
    if len(s) == 0:
        continue
    (sdir, sbase) = os.path.split(s)

    # actually use relative path
    key = os.path.splitext(s[(len(SOURCE_DIR)+1):])[0]

    printv('1:\t', key)

    # figure out here if we're actually in a multi-pager
    page_num = 1
    re_match = re.search(COLLATE_FMT, key)
    newkey = key # updated if multipager
    if re_match:
        newkey = re_match.group(1)
        if newkey not in multipagers:
            multipagers[newkey] = []
        multipagers[newkey].append((re_match.group(2),re_match.group(3)))
        printv("*** Found a multi-pager: {}, page {}".format(re_match.group(1), re_match.group(3)))
        page_num = int(re_match.group(3))


    # initialise
#    manifest[key] = []
    if not newkey in manifest:
        manifest[newkey] = {}

    submanifest = [] # pop variants in here instead

    # Iterate over variants...

    for variant in VARIANTS:

        auth_tag_var = ""
        print_tag_var = ""
        if variant[1]:
            auth_tag_var = auth_tag_full
        if variant[2]:
            print_tag_var = print_tag_full

        # We shall first output the auth'd SVGs to RENDER_DIR

        rdir = os.path.join(RENDER_DIR, sdir.replace(SOURCE_DIR + os.path.sep, ""))
        (r_tag_root, r_tag_ext) = os.path.splitext(sbase)
        # Pathnames of tagged SVGs
        r_tag = os.path.join(rdir, r_tag_root + "-" + variant[0] + r_tag_ext)

        # On checking file modification dates and skipping if 'no change':

        # Ideally we could not update the tagged SVG if it wouldn't change,
        # or at least not update its file modification date -- otherwise,
        # toggling output formats forces a full re-rendering.
        # Switching to/from alternate tags might also cause issues.
        # We have to handle this case by just speculatively tagging and
        # comparing to the existing file (if it exists)


        # OK. Create temp file and run sed into it for the tags
        # hmm. this runs once per output format right now.

        if not os.path.exists(rdir):
            # print(rdir)
            os.makedirs(rdir)

        # We should search the relevant file for the tag and skip
        # if we would normally substitute, but it doesn't exist

        if variant[1] and \
           int(subprocess.run(["grep", "-cF", AUTH_TAG, s],
                                             stdout=subprocess.PIPE)
                              .stdout) < 1:
            printv("No Auth Tag: skipping what would be", r_tag, sep='\t')
            notagcount += 1
            continue

        if variant[2] and \
           int(subprocess.run(["grep", "-cF", PRINT_TAG, s],
                                             stdout=subprocess.PIPE)
                              .stdout) < 1:
            printv("No Print Tag: skipping what would be", r_tag, sep='\t')
            notagcount += 1
            continue


        # Now it's sed time

        with tempfile.NamedTemporaryFile() as tmpfp:
            subprocess.run(["sed",
                            "-e", "s/" + re.escape(AUTH_TAG) + "/" + re.escape(auth_tag_var) + "/g",
                            "-e", "s/" + re.escape(PRINT_TAG) + "/" + re.escape(print_tag_var) + "/g",
                            s],
                           stdout=tmpfp)

            # Compare speculative and existing tagged SVGs
            if os.path.exists(r_tag):
                if filecmp.cmp(r_tag, tmpfp.name): # SVGs identical
                    printv("No change to", r_tag, sep="\t")
                else:
                    # The tagged SVG has changed: copy it over
                    printv("Updating", r_tag, sep="\t")
                    shutil.copy2(tmpfp.name, r_tag)
            else:
                # The tagged SVG now exists: copy it over
                printv("Updating", r_tag, sep="\t")
                shutil.copy2(tmpfp.name, r_tag)

        renderargs = []

        # Iterate over output formats...
        for ftype in FORMATS:
            # Pathname of output file
            r_out = os.path.join(rdir, r_tag_root + "-" + variant[0])  + "." + ftype

            submanifest.append(r_out[(len(RENDER_DIR)+1):])
            printv("2:\t", r_out[(len(RENDER_DIR)+1):])

            # Now check to see if output file is newer
            if os.path.exists(r_out):
                if os.path.getmtime(r_tag) <= os.path.getmtime(r_out):
                    printv("No change: skipping", r_out, sep="\t")
                    skipcount += 1
                    continue
            # (else:)
            updatecount += 1
            printv("Rendering", r_out, sep="\t")

            if ftype == "png":
                renderargs = ["-e", r_out]
            elif ftype == "pdf":
                renderargs = ["--export-dpi=300", "--export-text-to-path", "-A", r_out]

            # output ALL the things
            if len(renderargs): # this line is quite an important optimisation!
                inky = subprocess.run([BACKEND_PATH, "-z"]
                                      + renderargs
                                      + ["-f", r_tag],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
                printv(inky.stdout.decode())
                printv(inky.stderr.decode())

    # Finally, now that we're done with variants...
    manifest[newkey][page_num] = submanifest

# Here. we collate rendered PDFs.

printv(multipagers)

for mpkey in multipagers:
    # list of filenames to collate

    printv(mpkey)

    (mpkeyroot, mpkeyname) = os.path.split(mpkey)

    R_SUBDIR = os.path.join(RENDER_DIR, mpkeyroot)

    PDFs = subprocess.run(["find", R_SUBDIR, "-type", "f", "-name", mpkeyname+"*.pdf"],
                           stdout=subprocess.PIPE,
                           universal_newlines=True)\
            .stdout.strip().split(sep="\n")

    # We need a coherent ordering
    # keeping in mind that we probably have multiple tag variants to deal with

    tagset = {}

    for p in PDFs:
        proot = os.path.splitext(p)[0]
        #printv(proot)
        re_match = re.search(COLLATE_FMT, proot)
        # Note that this won't match the finished product
        if re_match:
            #printv((re_match.group(1), re_match.group(2), re_match.group(3), re_match.group(4)))
            tk = (re_match.group(1), re_match.group(4))
            if not tk in tagset:
                tagset[tk] = []
            tagset[tk].append((re_match.group(2), re_match.group(3)))
            # NB the int() cast above!
        else:
            #printv("no match here")
            pass

    for t in tagset:
        tagset[t] = sorted(tagset[t], key=lambda x: int(x[1]))
        # this little lambda trick sorts by the integer value of the digits
        # doubly tricky because they're normally strings (i.e. '11' before '2')
        # and because they're the second item in the tuples...
        paths = [''.join([t[0], i[0], i[1], t[1], ".pdf"]) for i in tagset[t]]
        printv(t, tagset[t], paths)

        res = subprocess.run([COLLATER, *paths, ''.join([*t, ".pdf"])])




with open(MANIFEST_FILE, 'w') as mf:
#    keys = sorted(manifest.keys())
    print(json.dumps(manifest), file=mf)


print("render.py:\t{} new renders performed.\t{} renders already up-to-date."
       .format(updatecount, skipcount), file=sys.stderr)

# this would've been a makefile,
# but `make` really doesn't like filenames with spaces in them
