from __future__ import print_function
import urllib.parse
import subprocess
import os.path
import re
import io
import PyPDF2
import json
import sys

AUTH_TAG = "PPAU_AUTH_TAG"
PRINT_TAG = "PPAU_PRINT_TAG"
SOURCE_DIR = "Artwork"
auth_file = "auth_tag.txt"
manifest_file = "MANIFEST.json"

seddy = "/bin/sed"
inky = "/usr/bin/inkscape"

def esc(str):
    '''XML escape, but forward slashes are also converted to entity references
       and whitespace control characters are converted to spaces'''
    from xml.sax.saxutils import escape
    return escape(str,  {'\n': ' ', '\t': ' ', '\b': ' ', '\r': ' ', '\c': ' ', '/': '&#47;'})

def application(env, start_response):
    head = ['200 OK', [('Content-Type','text/html')]]
    body = b""

    #print(env)

    doc_root = env['DOCUMENT_ROOT']
    page_root = os.path.dirname(env['PATH_INFO'])[1:] # drop leading /
    auth_path = os.path.join(doc_root, page_root, auth_file)
    manifest_path = os.path.join(doc_root, page_root, manifest_file)

    auth_repl = ""
    try:
        with open(auth_path, 'r') as af:
            auth_repl = esc(af.read())
    except Exception:
        print("Error reading authorisation tag file at", auth_path)
        head = ['500 Internal Server Error', [('Content-Type','text/html')]]

    # Load up the manifest
    # Trust the OS to keep both files in RAM cache.
    manifest = {}
    try:
        with open(manifest_path, 'r') as mf:
            manifest = json.load(mf)
    except Exception:
        print("Error loading manifest file at", manifest_path)
        head = ['500 Internal Server Error', [()]]

    # do intelligent things based on env['QUERY_STRING']
    query_dict = urllib.parse.parse_qs(env['QUERY_STRING'])
    #print(query_dict)

    # do appropriate things
    # we expect keys for name (a path fragment), printer tag and format

    qprint_tag = ""
    qfile = ""
    qformat = ""

    qkeys = query_dict.keys()

    if "printer" in qkeys:
        if query_dict["printer"]:
            qprint_tag = "Printed by " + esc(query_dict["printer"][0])

    if not "name" in qkeys:
        head = ['400 Bad Query', [('Content-Type','text/html')]]
    elif not query_dict["name"][0] in manifest.keys():
        head = ['404 Not Found', [('Content-Type', 'text/html')]]

    if not "format" in qkeys:
         head = ['400 Bad Query', [('Content-Type','text/html')]]
    elif not (query_dict["format"][0].upper() == "PDF"): # only support PDF now
         head = ['400 Bad Query', [('Content-Type','text/html')]]
    elif (query_dict["format"][0].upper() == "PDF") and not qprint_tag:
         head = ['400 Bad Query', [('Content-Type','text/html')]]

    if head[0] == '200 OK':
        # first see if we have a usable inkscape
        inkv = subprocess.Popen([inky, "-V", "--no-gui"],
                                 stdout=subprocess.PIPE
                                 ).stdout
        inkscape_version = "1"
        if "Inkscape 0.9" in inkv:
            inkscape_version = "0.9"

        if query_dict["format"][0].upper() == "PDF":
            # handle PDF
            head = ['200 OK', [('Content-Type', 'application/pdf')]]
            if inkscape_version == "1":
                qformat = "--export-type=pdf"
            else:
                qformat = "-A"
        # only support PDF export now

        # This is the un-fun part where we need multiple things rendered

        item = manifest[query_dict["name"][0]]

        pagenums = sorted([int(k) for k in item.keys()])

        merger = PyPDF2.PdfFileMerger()
        bodyIO = io.BytesIO()

        page_range = PyPDF2.PageRange(":")

        for pn in pagenums:

            qfile = os.path.join(doc_root, page_root, SOURCE_DIR, item[str(pn)][0][:-9] + ".svg")
            print(qfile, pn)
            # sed
            # the specific problem here is we also need to escape forward slashes
            authsub = "s/" + re.escape(AUTH_TAG) + "/" + re.escape(auth_repl) + "/g"
            printsub = "s/" + re.escape(PRINT_TAG) + "/" + re.escape(qprint_tag) +"/g"
#            print(authsub)
#            print(printsub)

            sed = subprocess.Popen([seddy,
                                    "-e", authsub,
                                    "-e", printsub,
                                    qfile],
                                    stdout=subprocess.PIPE)
            # inkscape
            inkscape_args = []
            if inkscape_version == "1":
                inkscape_args = [inky, "--export-dpi=300",
                                 qformat, "--pipe", "-o", "-"]
            elif inkscape_version == "0.9":
                inkscape_args = [inky, "-z", "--export-dpi=300",
                                 qformat, "/dev/stdout",
                                 "-f", "/dev/stdin"]
            #####

            inkscape = subprocess.Popen(inkscape_args,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=sed.stdout)
            sed.stdout.close() # as per docs for SIGPIPE
            outs, errs = inkscape.communicate()
            this_page = io.BytesIO(outs)
#            print('page', pn, 'is', len(outs), 'bytes')
#            print(errs)
            inkscape.kill() # anti zombie measures?

            merger.append(this_page, pages=page_range)

        # end of that for loop

        # Now get the merged file out
        merger.write(bodyIO)
        body = bodyIO.getvalue()

        head[1].append(('Content-Disposition', ('inline; filename="' + re.sub('[^0-9a-zA-Z-_.]+',
                        '-',
                        query_dict["name"][0] + '.' + query_dict["format"][0].lower() ) + '"'
                        )))

    # check head status again rather than an else, just in case something went wrong
    if not head[0] == '200 OK':
        body = (head[0] + " " + repr(query_dict)).encode('utf8')
        head[1] = [('Content-Type','text/html')] # reverts whatever we did with Content-Disposition

    #print(repr(head))
    start_response(head[0], head[1])
    return [body]