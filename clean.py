#!/usr/bin/env python3

################################################################################
#### ABOUT:                                                                 ####
#### remove old renders, while leaving those that are meant to be there     ####
################################################################################

RENDER_DIR = "Renders"                  # default: "Renders"
MANIFEST_FILE = "MANIFEST.json"         # default: "MANIFEST.json"

################################################################################
#### You shouldn't need to ever edit anything below this comment.           ####
################################################################################

VERSION = "0.0.2"

import subprocess
import argparse
import json
import os.path
import shutil
import sys
import logging

parser = argparse.ArgumentParser(description="Remove old renders, but keep current ones.", 
                                 prog="PPAU-Graphics Render Cleanup",
                                 epilog="For a complete cleanup, simply remove your render directory...")

parser.add_argument('-d', '--render_dir', dest='render_dir',
                    action='store', default=RENDER_DIR,
                    help="the directory containing the rendered files")

parser.add_argument('-m', '--manifest-file', dest='manifest',
                     action='store', default=MANIFEST_FILE,
                     help="the manifest JSON as output by render.py")
                    
parser.add_argument('--version', action='version', version='%(prog)s '+VERSION)


parser.add_argument('--verbose', action='count', help="tell me more", default=0)
parser.add_argument('--quiet', action='count', help="tell me less", default=0)
parser.add_argument('--log', type=argparse.FileType('a'), default=sys.stderr, help="file to log to (default: stderr)")

arguments = parser.parse_args()

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
    logging.critical(sep.join([str(x) for x in args]), **kwargs)
    sys.exit(code)

# we don't remove files, we remove whole subdirectories that aren't in the manifest

# manifest is keyed by e.g. a/b/c where a and b are directories, c is a source file name

keep_folders = set() 

with open(arguments.manifest, 'r') as mani:
    jm = json.load(mani)

    for k in jm.keys():
        keep_folders.add(os.path.dirname(k))


folders = subprocess.run(["find", RENDER_DIR, "-type", "d"],
                       stdout=subprocess.PIPE,
                       universal_newlines=True)\
        .stdout.strip().split(sep="\n")


total_deletions = 0
total_skips = 0

for f in folders:
    # remove Renders/ or equivalent off the front
    fbit = os.path.relpath(f, start=arguments.render_dir)

    if len(fbit) == 0 or fbit == ".":
        continue
        
    if fbit not in keep_folders:
        # it's possible that there are one or more subdirectories of fbit
        # that *are* in keep_folders though; if so, keep fbit
        
        subdir_ok = False
        
        for kf in keep_folders:
            if kf.startswith(fbit):
                subdir_ok = True
                break
        
        if subdir_ok:
            printv("skipping", fbit)
            total_skips += 1
            continue
        else:
            printv("Deleting:", f)
            try:
                shutil.rmtree(f)
            except Exception as e:
                printv(e.message, e.args)
            total_deletions += 1
            
printq("Performed", total_deletions, "deletions", "and skipped", total_skips)

