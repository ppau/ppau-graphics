# Python 3 not 2!  :)
import urllib.parse
import subprocess
import os.path

AUTH_TAG = "PPAU_AUTH_TAG"
PRINT_TAG = "PPAU_PRINT_TAG"
SOURCE_DIR = "/var/www/abjago.net/html/ppau-graphics/Artwork"
auth_file = "/var/www/abjago.net/html/ppau-graphics/auth_tag.txt"

seddy = "/bin/sed"
inky = "/usr/bin/inkscape"

def application(env, start_response):
    head = ['', [()]]	
    body = b""

    auth_repl = ""
    with open(auth_file, 'r') as af:
	auth_repl = af.read().replace('\n', " ")   

    # do intelligent things based on env['QUERY_STRING']

    query_dict = urllib.parse.parse_qs(env['QUERY_STRING'])

    # do appropriate things
    # we expect keys for name (a path fragment), printer tag and format

    qprint_tag = ""
    qfile = ""
    qformat = ""    

    qkeys = list(query_dict.keys())

    if "printer" in qkeys:
        if query_dict["printer"]:
            qprint_tag = "Printed by " + query_dict["printer"][0]

    if not "name" in qkeys:
        head = ['400 Bad Query', [('Content-Type','text/html')]] 
    elif not os.path.exists(os.path.join(SOURCE_DIR, query_dict["name"][0] + ".svg")):
        head = ['404 Not Found', [('Content-Type', 'text/html')]]

    if not "format" in qkeys:
         head = ['400 Bad Query', [('Content-Type','text/html')]] 	
    elif not ((query_dict["format"][0].upper() == "PDF") or (query_dict["format"][0].upper() == "PNG")):
         head = ['400 Bad Query', [('Content-Type','text/html')]] 
    elif (query_dict["format"][0].upper() == "PDF") and not qprint_tag:
         head = ['400 Bad Query', [('Content-Type','text/html')]] 
    else:
        if query_dict["format"][0].upper() == "PDF":
            # handle PDF
            head = ['200 OK', [('Content-Type', 'application/pdf')]]
            qformat = "-A"
        elif query_dict["format"][0].upper() == "PNG":
            # handle PNG
            head = ['200 OK', [('Content-Type', 'image/png')]]
            qformat = "-e" 
 
        qfile = os.path.join(SOURCE_DIR, query_dict["name"][0] + ".svg")        
        print(qfile)
        # sed
        sed = subprocess.Popen([seddy,
                                "-e", "s/"+AUTH_TAG+"/"+auth_repl+"/g", 
                                "-e", "s/"+PRINT_TAG+"/"+qprint_tag+"/g", 
                                qfile], 
                                stdout=subprocess.PIPE)
        # inkscape
        inkscape = subprocess.Popen([inky, "-z", 
                                     qformat, "/dev/stdout",
                                     "-f", "/dev/stdin"],
                                     stdout=subprocess.PIPE,
                                     stdin=sed.stdout)

        sed.stdout.close() # as per docs for SIGPIPE
        body = inkscape.communicate()[0]

        print(type(body))


    if not (head[0][0:3] == '200'):
        body = head[0] + " " + repr(query_dict).encode('utf8')

    start_response(head[0], head[1])
    return [body]

