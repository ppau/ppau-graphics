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
AUTH_TAG_FILE_BASIC = "auth_tag_basic.txt"    # default: "auth_tag_basic.txt"
SKIP_PREFIX = "__"

RENDER_DIR = "Renders"                  # default: "Renders"
SITE_ROOT = '.'
# Your nginx setup may require site roots on-server to be absolute
# So use --site-root "https://example.tld/ppau-graphics"

POSTER_REPLACE_TAG = "PPAU_POSTERS_HERE"
PAMPHLET_REPLACE_TAG = "PPAU_PAMPHLETS_HERE"
ONLINE_REPLACE_TAG = "PPAU_ONLINES_HERE"

CONVERT = "convert"
CONVERT_PATH = ""

preconvargs = []
convargs = ["-background", "white", "-flatten", "-resize", "x400", "-quality", "80"]
# ^^^ give it a white bg if needed, maintain aspect ratio but make it 400px high

VERBOSE = False
VERSION = '0.5.5'

import json
import os.path
import sys
import subprocess
import re
import argparse
import datetime
import logging


# Handle our no longer especially minimal set of CL Args

argparser = argparse.ArgumentParser(description="Generate a static index page from a template, with JPEGs for the thumbnails.")
argparser.add_argument('--manifest-file', default=MANIFEST_FILE, help="Path to the manifest JSON file")
argparser.add_argument('--template-file', default=TEMPLATE_FILE, help="Path to the template HTML file")
argparser.add_argument('--index-file', default=INDEX_FILE, help="Path to put the generated index HTML file")
argparser.add_argument('--render-dir', default=RENDER_DIR, help="Path to the render directory")
argparser.add_argument('--site-root', default=SITE_ROOT, help="Path for the root of the index page; default is `"+SITE_ROOT+"`")
argparser.add_argument('--wsgi-url', default=None, help="Path for WSGI request handler; default is `{site root}/wsgi`")
argparser.add_argument('--poster-replace-tag', default=POSTER_REPLACE_TAG, help="The string in the template to be replaced by the poster content")
argparser.add_argument('--pamphlet-replace-tag', default=PAMPHLET_REPLACE_TAG, help="The string in the template to be replaced by the pamphlet content")
argparser.add_argument('--online-replace-tag', default=ONLINE_REPLACE_TAG, help="The string in the template to be replaced by the online-only content")
argparser.add_argument('--auth-tag-file-basic', dest='auth_tag_file_basic', action='store', default=AUTH_TAG_FILE_BASIC, help="The file containing the authorisation text specifying only a town/city (for digital material).")
argparser.add_argument('--skip-prefix', default=SKIP_PREFIX, help="Skip items starting with this prefix; default is '"+SKIP_PREFIX+"'; pass an empty string for no skipping")
argparser.add_argument('--version', action='version', version=VERSION)
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
    logging.critical(sep.join([str(x) for x in args]), **kwargs)
    sys.exit(code)

print("Command line arguments:", arguments)

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
            failure("could not find `"+ CONVERT +"`!")
    else:
        failure("could not find `"+ CONVERT +"`!")



# General structure: we need to generate a sequence of
#   <div><img><p>caption</p></div>'s.


poster_replacement_str = ''
pamphlet_replacement_str = ''
online_replacement_str = ''
src_str = ""
out_str = ""

#printv("\ntitle", "count", "thumbnail path", sep="\t")

# Collate posters.
with open(arguments.manifest_file, 'r') as mani_fp:
    manifest = json.load(mani_fp)

    #printv("Entire Manifest:\n", manifest)

    # Everything from here down needs a major rewrite
    # to be compatible with the new Manifest format

    # (New) Manifest structure:
    # { "key" : {
    #             "1" : [
    #                 "path/to/file_p1-auth.pdf",
    #                 "path/to/file_p1-auth.png",
    #                 ...
    #               ],
    #             "2" : [
    #                 "path/to/file_p2-auth.pdf",
    #                 "path/to/file_p2-auth.png",
    #                 ...
    #               ],
    #           }
    # }

    for mkey in sorted(manifest.keys()):

        item = manifest[mkey]

        printv("Item", mkey, ":\n", item)

        authFlagged = False
        printFlagged = False
        ourfile = None

        ## Iterate over the items (of the first page, anyway)
        ## to determine what tags it has.
        for i in item['1']:
            authFlagged |= ("-auth.png" in os.path.split(i)[1])
            printFlagged |= ("-both.pdf" in os.path.split(i)[1])
            if authFlagged and not ourfile: # special sauce
                ourfile = i            

        if arguments.skip_prefix:
            skipme = False
            for k in mkey.split('/'):
                if k.startswith(arguments.skip_prefix):
                    print("Skipping", mkey, "for filename including the skip prefix", arguments.skip_prefix)
                    skipme = True
                    break
            if skipme:
                continue

        if not (authFlagged or printFlagged):
            printv("Skipping", mkey, "as no tags are included")
            continue

        printv(mkey, authFlagged, printFlagged)

        posterFlag = printFlagged and len(item) == 1
        pamphletFlag = printFlagged and len(item) > 1
        onlineFlag = authFlagged and not printFlagged

        #continue
        if not ourfile:
            ourfile = item['1'][0]
        r_in = os.path.join(arguments.render_dir, ourfile)
        r_out = os.path.join(arguments.render_dir, ourfile[0:-4] + "_preview" + ".jpg")

        dlname = os.path.splitext(os.path.basename(ourfile))[0][0:-5]
        caption = os.path.split(mkey)[1]

#        printv(k, len(m[k]), r_in, r_out, ourfile, sep="\t") # [1] is *-auth.png

        
        if not (os.path.exists(r_out) and (os.path.getmtime(r_in) <=  os.path.getmtime(r_out))):
            flippy = subprocess.run([CONVERT_PATH] + preconvargs + [r_in]
                                  + convargs
                                  + [r_out],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            printv("stdout from ^^^:", flippy.stdout.decode())
            printv("stderr from ^^^:", flippy.stderr.decode())

        if posterFlag:
            poster_replacement_str += '<div>\r\n        '+\
            '<img src="'+arguments.site_root+'/'+r_out+'" alt="'+mkey+'">'+'\r\n        '+ \
            '<p class="caption"><a href="'+arguments.site_root+'/'+r_in+'" download="'+dlname+'">'+caption+'</a></p>\r\n      </div>\r\n'
        elif pamphletFlag:
            pamphlet_replacement_str += '<div>\r\n        '+\
            '<img src="'+arguments.site_root+'/'+r_out+'" alt="'+mkey+'">'+'\r\n        '+ \
            '<p class="caption"><a href="'+arguments.site_root+'/'+r_in+'" download="'+dlname+'">'+caption+'</a></p>\r\n' + \
            '<p class="caption">Page:&nbsp;&nbsp;'
            for p in sorted(item, key=lambda x: int(x)):
                link = os.path.join(arguments.render_dir, item[str(p)][0])
                dl = os.path.splitext(os.path.basename(link))[0][0:-5]
                pamphlet_replacement_str += '<a href="'+arguments.site_root+'/'+link+'" download="'+dl+'">'+str(p)+'</a>&nbsp;&nbsp;'
            pamphlet_replacement_str += '</p>      </div>\r\n'
        elif onlineFlag:
            online_replacement_str += '<div>\r\n        '+\
            '<a href="'+arguments.site_root+'/'+r_in+'" download="'+dlname+'">'+\
            '<img src="'+arguments.site_root+'/'+r_out+'" alt="'+mkey+'">'+'\r\n        '+ \
            '<p class="caption">'+caption+'</p></a>\r\n'
            if len(item) > 1:
                online_replacement_str += '<p class="caption">Page:&nbsp;&nbsp;'
                for p in sorted(item, key=lambda x: int(x)):
                    link = os.path.join(arguments.render_dir, item[str(p)][0])
                    dl = os.path.splitext(os.path.basename(link))[0][0:-5]
                    online_replacement_str += '<a href="'+arguments.site_root+'/'+link+'" download="'+dl+'">'+str(p)+'</a>&nbsp;&nbsp;'
                online_replacement_str += '</p>'
            online_replacement_str += '      </div>\r\n'


printv("\nPoster Replacement String:\n", poster_replacement_str)
printv("\nPamphlet Replacement String:\n", pamphlet_replacement_str)
printv("\nOnline Replacement String:\n", online_replacement_str)


with open(arguments.template_file) as templatefp:
    out_str = templatefp.read().replace(arguments.poster_replace_tag, poster_replacement_str)
    out_str = out_str.replace(arguments.pamphlet_replace_tag, pamphlet_replacement_str)
    out_str = out_str.replace(arguments.online_replace_tag, online_replacement_str)

## Get and add some metadata 

with open(arguments.auth_tag_file_basic) as atfbfp:
    atb = atfbfp.read()
    out_str = out_str.replace("AUTH_TAG_BASIC", atb)

out_str = out_str.replace("META_TIMESTAMP", datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z")

gitty = subprocess.run(["git", "rev-parse", "--short", "HEAD"], stdout=subprocess.PIPE)
# N.B. --short will actually use more than [n = 7] characters if there's a collision
#   these are expected to be kept up to date, and GitHub handles prefixes sensibly too
#   so it should all Just Work (TM).
hashy = gitty.stdout.decode().strip()
out_str = out_str.replace("GIT_HASH", hashy)

site_root = "" if (arguments.site_root == ".") else (arguments.site_root.rstrip('/') + '/')
out_str = out_str.replace("SITE_ROOT", site_root)

wsgi_url = (site_root + 'wsgi') if (arguments.wsgi_url is None) else arguments.wsgi_url
out_str = out_str.replace("WSGI_URL", wsgi_url)

## Print ##
with open(arguments.index_file, 'w') as indexfp:
    print(out_str, file=indexfp)
