import urllib.parse
import subprocess
import os.path
import re
import io
import PyPDF2
import json

AUTH_TAG = "PPAU_AUTH_TAG"
PRINT_TAG = "PPAU_PRINT_TAG"
SOURCE_DIR = "/var/www/abjago.net/html/ppau-graphics/Artwork"
auth_file = "/var/www/abjago.net/html/ppau-graphics/auth_tag.txt"
manifest_file = "/var/www/abjago.net/html/ppau-graphics/MANIFEST.json"

seddy = "/bin/sed"
inky = "/usr/bin/inkscape"

def application(env, start_response):
    head = ['', [()]]
    body = b""

    auth_repl = ""
    with open(auth_file, 'r') as af:
        auth_repl = af.read().replace('\n', " ")

    # Load up the manifest
    # Trust the OS to keep both files in RAM cache.
    manifest = {}
    with open(manifest_file, 'r') as mf:
        manifest = json.load(mf)

    # do intelligent things based on env['QUERY_STRING']

    query_dict = urllib.parse.parse_qs(env['QUERY_STRING'])

    # do appropriate things
    # we expect keys for name (a path fragment), printer tag and format

    qprint_tag = ""
    qfile = ""
    qformat = ""

    qkeys = query_dict.keys()

    if "printer" in qkeys:
        if query_dict["printer"]:
            qprint_tag = "Printed by " + query_dict["printer"][0]

    if not "name" in qkeys:
        head = ['400 Bad Query', [('Content-Type','text/html')]]
    elif not query_dict["name"][0] in manifest.keys():
#    elif not os.path.exists(os.path.join(SOURCE_DIR, query_dict["name"][0] + ".svg")):
        head = ['404 Not Found', [('Content-Type', 'text/html')]]

    if not "format" in qkeys:
         head = ['400 Bad Query', [('Content-Type','text/html')]]
    elif not ((query_dict["format"][0].upper() == "PDF") or (query_dict["format"][0].upper() == "PNG")):
         head = ['400 Bad Query', [('Content-Type','text/html')]]
    elif (query_dict["format"][0].upper() == "PDF") and not qprint_tag:
         head = ['400 Bad Query', [('Content-Type','text/html')]]
    else:
        # first see if we have a usable inkscape
        inkv = subprocess.Popen([inky, "-V", "--no-gui"],
                                 stdout=subprocess.PIPE
                                 ).stdout
        inkscape_version = "1.0"
        if "Inkscape 0.9" in inkv:
            inkscape_version = "0.9"
         
        if query_dict["format"][0].upper() == "PDF":
            # handle PDF
            head = ['200 OK', [('Content-Type', 'application/pdf')]]
            if inkscape_version == "1.0":
                qformat = "--export-type=pdf"
            else:
                qformat = "-A"
        elif query_dict["format"][0].upper() == "PNG":
            # handle PNG
            head = ['200 OK', [('Content-Type', 'image/png')]]
            if inkscape_version == "1.0":
                qformat = "--export-type=png"
            else:
                qformat = "-A"

        # This is the un-fun part where we need multiple things rendered

        item = manifest[query_dict["name"][0]]

        pagenums = sorted([int(k) for k in item.keys()])

        # quick catch to ensure we don't try to make multi page PNGs
        if qformat == "-e":
            pagenums = [1]

    #print("pagenums", pagenums)

        merger = PyPDF2.PdfFileMerger()
        bodyIO = io.BytesIO()

	range = PyPDF2.PageRange(":")

        for pn in pagenums:

            #qfile = os.path.join(SOURCE_DIR, query_dict["name"][0] + ".svg")
            qfile = os.path.join(SOURCE_DIR, item[str(pn)][0][:-9] + ".svg")
            print qfile, pn
            # sed
            sed = subprocess.Popen([seddy,
                                    "-e", "s/" + re.escape(AUTH_TAG) + "/" + re.escape(auth_repl) + "/g",
                                    "-e", "s/" + re.escape(PRINT_TAG) + "/" + re.escape(qprint_tag) +"/g",
                                    qfile],
                                    stdout=subprocess.PIPE)
            # inkscape
            inkscape_args = []
            if inkscape_version == "1.0":
                inkscape_args = [inky, "--export-dpi=300",   # if on inkscape < 1.0 you'll likely want -z
                                 qformat, "--pipe", "-o", "-"]
            else if inkscape_version = "0.9":
                inkscape_args = [inky, "-z", "--export-dpi=300",
                                 qformat, "/dev/stdout",
                                 "-f", "/dev/stdin"]
            #####

            inkscape = subprocess.Popen(inkscape_args,
                             stdout=subprocess.PIPE,
                             stdin=sed.stdout)
            sed.stdout.close() # as per docs for SIGPIPE
            this_page = io.BytesIO(inkscape.communicate()[0])

            merger.append(this_page, pages=range)

        # end of that for loop

        # Now get the merged file out
        merger.write(bodyIO)
        body = bodyIO.getvalue() #.encode() # magic

        head[1].append(('Content-Disposition', 'inline; filename="' + re.sub('[^0-9a-zA-Z-_\.]+', '-', query_dict["name"][0] + '.' + query_dict["format"][0].lower() ) + '"'))

        ##print type(body)
        #print("body length", len(body))

    if not (head[0][0:3] == '200'):
        body = head[0] + " " + repr(query_dict).encode('utf8')
        head[1] =  [('Content-Type','text/html')] # reverts whatever we did with Content-Disposition

    start_response(head[0], head[1])
    return [body]
