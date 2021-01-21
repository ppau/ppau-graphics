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
BACKEND_PATHS = ["/Applications/Inkscape.app/Contents/Resources/bin/inkscape", "/Applications/Inkscape.app/Contents/MacOS/inkscape", "/usr/bin/inkscape"]
COLLATER_PATH = "/usr/bin/pdfunite"

# If the paths below are relative, this file is assumed to be in the
# project's root directory.

SOURCE_DIR = "Artwork"                  # default: "Artwork"
RENDER_DIR = "Renders"                  # default: "Renders"

AUTH_TAG_FILE = "auth_tag.txt"          # default: "auth_tag.txt"
PRINT_TAG_FILE = "print_tag.txt"        # default: "print_tag.txt"

AUTH_TAG_FILE_BASIC = "auth_tag_basic.txt"    # default: "auth_tag_basic.txt"


# The text below is found, and replaced with the content of the relevant
# file listed above. Neither replaced text may be an SVG tag, for obvious reasons.

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

#### Currently only PNG (screen) and PDF (print) supported                  ####

SCREEN_FORMATS = ["png"]
PRINT_FORMATS = ["pdf"]

        #   (name, include auth tag, include print tag, media formats)
VARIANTS = [("auth", True, False, SCREEN_FORMATS),                # 'basic'
            ("both", True, True, PRINT_FORMATS),                  # 'full'
            ("none", False, False, SCREEN_FORMATS+PRINT_FORMATS)] # 'none'
        # NB: it's absurd to include a print tag but not an auth tag.


# Manifest output file

MANIFEST_FILE = "MANIFEST.json"

################################################################################
#### End users shouldn't need to ever edit anything below this comment.     ####
################################################################################

VERSION = "0.5.4" 

BACKEND = "inkscape"
COLLATER = "pdfunite"
BACKEND_PATH = ""

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
import io

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

parser.add_argument('--auth_tag_file_basic', dest='auth_tag_file_basic',
                    action='store', default=AUTH_TAG_FILE_BASIC,
                    help="The file containing the authorisation text\
                    specifying only a town/city (for digital material).")

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
AUTH_TAG_FILE_BASIC = args.auth_tag_file_basic
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

    if not os.path.isabs(AUTH_TAG_FILE_BASIC):
        AUTH_TAG_FILE_BASIC = os.path.join(sys.path[0], AUTH_TAG_FILE_BASIC)

    if not os.path.isabs(PRINT_TAG_FILE):
        PRINT_TAG_FILE = os.path.join(sys.path[0], PRINT_TAG_FILE)


# Just a little helper function
def printv(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs, file=sys.stderr)

printv("ppau-graphics, render script version:", VERSION)

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
            print("ERROR: could not find "+ BACKEND +"!", file=sys.stderr)
            sys.exit(1)
    else:
        print("ERROR: could not find "+ BACKEND +"!", file=sys.stderr)
        sys.exit(1)

# Ensure Inkscape 1.0 
if 'inkscape' in BACKEND_PATH:
    vtext = subprocess.run([BACKEND_PATH, "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
    if b"Inkscape 0." in vtext:
        print("ERROR: requires Inkscape 1.0 or higher", file=sys.stderr)
        sys.exit(1)
    elif b"Inkscape 1." in vtext:
        print("SUCCESS: able to use Inkscape 1.0 or higher", file=sys.stderr)

# Go find COLLATER if we haven't already
if not os.path.exists(COLLATER_PATH) and not NO_COLLATE:
    printv("{} not found at specified path {}".format(COLLATER, COLLATER_PATH))

    if os.name == "posix":
        collatertry = subprocess.run(["which", COLLATER],
                stdout=subprocess.PIPE,
                universal_newlines=True)\
                .stdout.strip()
        if collatertry:
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
auth_tag_basic = ""
print_tag_full = ""

# basic can fall back on full if it exists

try:
    with open(AUTH_TAG_FILE) as atfp:
        auth_tag_full = atfp.read().strip()
        printv("full", auth_tag_full)
except FileNotFoundError:
    print("Authorisation tag file not found!",
          "No substitution will be performed.")
    auth_tag_full = AUTH_TAG

try:
    with open(AUTH_TAG_FILE_BASIC) as atfp:
        auth_tag_basic = atfp.read().strip()
except FileNotFoundError:
    print("Basic auth tag file not found! Falling back on", 
          AUTH_TAG_FILE)
    auth_tag_basic = auth_tag_full
    
try:
    with open(PRINT_TAG_FILE) as ptfp:
        print_tag_full = ptfp.read().strip()
        printv(print_tag_full)
except FileNotFoundError:
    print("Printing tag file not found!",
          "No substitution will be performed.")
    print_tag_full = PRINT_TAG


# Optimise: by caching the auth and print tags
# update the cachefile only if needed
# then later, if every cachefile modification is older than sourcefile modification,
# there's no need to update the sourcefile

atf_path = os.path.normpath(os.path.join(os.path.join(RENDER_DIR, ".auth_tag_full_cache")))
atb_path = os.path.normpath(os.path.join(os.path.join(RENDER_DIR, ".auth_tag_basic_cache")))
ptf_path = os.path.normpath(os.path.join(os.path.join(RENDER_DIR, ".print_tag_full_cache")))

# xxx_cacheable iff the cache has the same contents as the current value
atf_cacheable = False
atb_cacheable = False
ptf_cacheable = False

if os.path.exists(atf_path):
    with open(atf_path) as fp:
        if auth_tag_full == fp.read().strip():
            atf_cacheable = True
        else:
        	print("ATF wasn't cacheable")

if not atf_cacheable:
    with open(atf_path, 'w') as fp:
        print(auth_tag_full, file=fp)

if os.path.exists(atb_path):
    with open(atb_path) as fp:
        if auth_tag_basic == fp.read().strip():
            atb_cacheable = True
        else:
        	print("ATB wasn't cacheable")


if not atb_cacheable:
    with open(atb_path, 'w') as fp:
        print(auth_tag_basic, file=fp)

if os.path.exists(ptf_path):
    with open(ptf_path) as fp:
        if print_tag_full == fp.read().strip():
            ptf_cacheable = True
        else:
        	print("PTF wasn't cacheable")

if not ptf_cacheable:
    with open(ptf_path, 'w') as fp:
        print(print_tag_full, file=fp)

atf_mod = os.path.getmtime(atf_path)
atb_mod = os.path.getmtime(atb_path)
ptf_mod = os.path.getmtime(ptf_path)

# We also want to keep a manifest of what we've done.
# {file basename, [paths to renders...]}
# but we don't actually want absolute pathnames for that
# we want them relative to the Source and Render dirs
manifest = {}

multipagers = {}

skipcount = 0
updatecount = 0
notagcount = 0

# Small amount of Inkscape funzies. 
# Make shell mode work, part 1
commands = io.StringIO()


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


    # Quickly figure out some things
    has_auth_tag = int(subprocess.run(["grep", "-cF", AUTH_TAG, s],
                                             stdout=subprocess.PIPE).stdout) >= 1
    has_print_tag = int(subprocess.run(["grep", "-cF", PRINT_TAG, s],
                                             stdout=subprocess.PIPE).stdout) >= 1
    # initialise
    if not newkey in manifest:
        manifest[newkey] = {}

    submanifest = [] # pop variants in here instead

    # Iterate over variants...

    for variant in VARIANTS:

        FORMATS = variant[3]
        auth_tag_var = ""
        print_tag_var = ""
        if variant[1]: # default to basic
            auth_tag_var = auth_tag_basic
        if variant[2]: # if we need a print tag, we need a full auth tag
            print_tag_var = print_tag_full
            auth_tag_var = auth_tag_full # override

        # We shall first output the auth'd SVGs to RENDER_DIR

        #rdir = os.path.join(RENDER_DIR, sdir.replace(SOURCE_DIR + os.path.sep, "")) 
        # there's a bug about where outputs go and I suspect it's this line ^^
        ## sometimes SOURCE_DIR already has a trailing path separator and sdir doesn't
        sfrag = sdir.replace(SOURCE_DIR.strip(os.path.sep), "").strip(os.path.sep)
        rdir = os.path.normpath(os.path.join(RENDER_DIR, sfrag))
        (r_tag_root, r_tag_ext) = os.path.splitext(sbase)
        # Pathnames of tagged SVGs
        r_tag = os.path.join(rdir, r_tag_root + "-" + variant[0] + r_tag_ext)
        printv("sdir:", sdir, "sfrag:", sfrag, "rdir:", rdir, "r_tag", r_tag)
        #exit()

        # OK. Create temp file and run sed into it for the tags
        # hmm. this runs once per output format right now.

        if not os.path.exists(rdir):
            # print(rdir)
            os.makedirs(rdir)

        # We should search the relevant file for the tag and skip
        # if we would normally substitute, but it doesn't exist
        
        if variant[1]:
            if not has_auth_tag:
                printv("No Auth Tag: skipping what would be", r_tag, sep='\t')
                notagcount += 1
                continue

        if variant[2]: 
            if not has_print_tag:
                printv("No Print Tag: skipping what would be", r_tag, sep='\t')
                notagcount += 1
                continue
                
        if (not (variant[1] or variant[2])) and (has_auth_tag or has_print_tag):
            printv("No need for 'None' variant: skipping", r_tag, sep='\t')
            continue

        # Iterate over output formats...
        for ftype in FORMATS:
            # Pathname of output file
            r_out = os.path.join(rdir, r_tag_root + "-" + variant[0])  + "." + ftype

            submanifest.append(r_out[(len(RENDER_DIR)+1):])
            printv("2:\t", r_out[(len(RENDER_DIR)+1):])


            # We also skip if the modification dates say we can
        
            if os.path.exists(r_tag) and atf_cacheable and atb_cacheable and \
                    ((ptf_cacheable and variant[2]) or not variant[2]) and \
                    (os.path.getmtime(r_tag) < atf_mod) and (os.path.getmtime(s) < atf_mod):
                printv("Already done: Skipping what would be", r_tag, sep='\t')
                skipcount += 1
                # still have to make sure this goes into the manifest!
            
                continue
            else:
                printv("Updating", r_tag, sep='\t')     
                with open(r_tag, 'w') as tagfp:
                    subprocess.run(["sed",
                                    "-e", "s/" + re.escape(AUTH_TAG) + "/" + re.escape(auth_tag_var) + "/g",
                                    "-e", "s/" + re.escape(PRINT_TAG) + "/" + re.escape(print_tag_var) + "/g",
                                    s],
                                   stdout=tagfp)

            renderargs = []


            # Now check to see if output file is newer
            if os.path.exists(r_out):
                if os.path.getmtime(r_tag) <= os.path.getmtime(r_out):
                    #printv("No change: skipping", r_out, sep="\t")
                    skipcount += 1
                    continue
            # (else:)
            updatecount += 1
            #printv("Rendering", r_out, sep="\t")

            if ftype == "png":
                renderargs.append("export-type:png; export-background-opacity:255;")
            if ftype == "pdf":
                renderargs.append("export-dpi:300; export-text-to-path:true; export-type:pdf;")
            
            print("file-open:"+r_tag+"; "+" ".join(renderargs)+" export-do; file-close;", file=commands)


    # Finally, now that we're done with variants...
    manifest[newkey][page_num] = submanifest

# Actually render things!
print('quit', file=commands)
printv("Rendering everything...")
inky = subprocess.run([BACKEND_PATH, "--shell"],
                      input=commands.getvalue(),
                      stdout=subprocess.PIPE,
                      stderr=subprocess.PIPE,
                      universal_newlines=True)  
    
# if we don't capture output, it gets printed to CLI
if inky.returncode != 0:      
    printv(inky.stdout)
    printv(inky.stderr)


# Cache auth and print tags... but only if they've changed
with open(os.path.join(RENDER_DIR, ".auth_tag_full_cache"), 'w') as fp:
    print(auth_tag_full, file=fp)

with open(os.path.join(RENDER_DIR, ".auth_tag_basic_cache"), 'w') as fp:
    print(auth_tag_basic, file=fp)

with open(os.path.join(RENDER_DIR, ".print_tag_cache"), 'w') as fp:
    print(print_tag_full, file=fp)


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
