#! /usr/bin/python3


def main():

    ### Download and install fonts ###

    # all known downloadable fonts
    # {"url": ["providesA", "providesB"]}
    LINKS = {
        "https://dl.dafont.com/dl/?f=airstream": ["Airstream"],
        "https://dl.dafont.com/dl/?f=deftone_stylus": ["Deftone Stylus"],
        "http://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip": [
            "DejaVu"
        ],  # inc. all
        "https://bboxtype.com/downloads/Fira/Download_Folder_FiraSans_4301.zip": [
            "Fira Sans"
        ],  # inc. compressed, condensed
        "https://github.com/ppau/gehen-fonts/raw/gh-pages/gehen-sans-otf-0.4.tar.gz": [
            "Gehen Sans"
        ],
        "https://indestructibletype.com/Jost.zip": ["Jost*", "Jost"],
        "https://github.com/liberationfonts/liberation-fonts/files/4743886/liberation-fonts-ttf-2.1.1.tar.gz": [
            "Liberation"
        ],
        "https://dl.dafont.com/dl/?f=minecraft": ["Minecraft"],
        "https://fonts.google.com/download?family=Open%20Sans": ["Open Sans"],
        "https://fonts.google.com/download?family=Open%20Sans%20Condensed": [
            "Open Sans Condensed"
        ],
        "https://fonts.google.com/download?family=Roboto%20Slab": ["Roboto Slab"],
        "https://dl.dafont.com/dl/?f=showtime": ["Showtime"],
        "https://github.com/adobe-fonts/source-serif-pro/releases/download/3.001R/source-serif-pro-3.001R.zip": [
            "Source Serif Pro"
        ],
        "https://www.ffonts.net/VIDEO-PIRATE.font.zip": ["VIDEO PIRATE"],
        "https://dl.dafont.com/dl/?f=lazer84": ["lazer84"],
    }

    # Some fonts are installable as Apt packages
    # (except the Microsoft core fonts, which need multiverse and are handled specially)
    # note that sources for these should also be included in LINKS for non-apt systems
    APTS = [
        "fonts-dejavu",
        "fonts-liberation2",
    ]

    FONTDIR = "/usr/local/share/fonts"

    #### Below this line is the actual script and should not need editing ##########

    import os
    import sys
    import subprocess
    import shutil
    import tempfile
    import urllib.parse
    import urllib.request
    import cgi
    import shlex
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="download and install the fonts")
    parser.add_argument(
        "-k", "--links", help="just output all the download links", action="store_true"
    )

    parser.add_argument("--verbose", action="count", help="tell me more", default=0)
    parser.add_argument("--quiet", action="count", help="tell me less", default=0)
    parser.add_argument(
        "--log",
        type=argparse.FileType("a"),
        default=sys.stderr,
        help="file to log to (default: stderr)",
    )

    arguments = parser.parse_args()

    __loglevel = logging.INFO
    if arguments.quiet > arguments.verbose:
        __loglevel = logging.WARNING
    elif arguments.quiet < arguments.verbose:
        __loglevel = logging.DEBUG

    logging.basicConfig(
        stream=arguments.log,
        level=__loglevel,
        format="%(levelname)s: %(message)s"
        if arguments.log.name == "<stderr>"
        else "%(asctime)s %(levelname)s: %(message)s",
    )

    def printv(*args, sep=" ", **kwargs):
        logging.debug(sep.join([str(x) for x in args]), **kwargs)

    def printq(*args, sep=" ", **kwargs):
        logging.info(sep.join([str(x) for x in args]), **kwargs)

    def failure(*args, sep=" ", code=1, **kwargs):
        logging.critical(sep.join([str(x) for x in args]), **kwargs)
        sys.exit(code)

    if arguments.links or sys.platform.startswith("windows"):
        if sys.platform.startswith("windows"):
            print(
                "The rest of this script isn't for Windows users. Sorry about that. Here's all the links:"
            )
        for k in LINKS.keys():
            print(k)
        exit(0)

    printq("Please note that this script requires the use of sudo.")

    if sys.platform.startswith("darwin"):
        FONTDIR = os.path.join(os.path.expanduser("~"), "Library", "Fonts")

    fccachetry = subprocess.run(
        ["which", "fc-cache"], stdout=subprocess.PIPE, universal_newlines=True
    ).stdout.strip()

    if not fccachetry:
        # Just dump the files to cwd()/ppau-graphics-fonts
        FONTDIR = os.path.join(os.getcwd(), "ppau-graphics-fonts")

    def prompt(cmd):
        print(">>>>>", cmd)
        os.system(cmd)

    #### Figure out what's missing

    listicle = set(
        subprocess.run(
            ["python3", "list_fonts.py", "-m"], stdout=subprocess.PIPE, text=True
        )
        .stdout.strip()
        .split("\n")
    )

    # deprecated: list_fonts now excludes sans-serif itself (and maybe others in the future)
    # if "sans-serif" in listicle:
    #     listicle.remove("sans-serif")

    printq(len(listicle), "missing fonts...")

    def match(name, listy):
        nl = name.lower()
        for ll in listy:
            lll = ll.lower()
            if nl in lll:
                return True
            elif lll in nl:
                return True
        return False

    #### Do the package installs ####
    # bail if need be

    if sys.platform.startswith("linux"):

        apttry = subprocess.run(
            ["which", "apt-get"], stdout=subprocess.PIPE, universal_newlines=True
        ).stdout.strip()

        if apttry:
            if not fccachetry:
                prompt("sudo apt-get -y install fontconfig")

            # now for the mainline apt install run
            prompt("sudo apt-get -y install " + " ".join(APTS))

            # and ms core
            msc = False
            for font in [
                "Arial",
                "Andale Mono",
                "Courier New",
                "Georgia",
                "Impact",
                "Trebuchet",
                "Verdana",
            ]:
                msc |= match(font, listicle)

            if msc:
                prompt("sudo add-apt-repository multiverse")
                prompt("sudo apt-get update")
                prompt("sudo apt-get -y install ttf-mscorefonts-installer")
        else:
            printq(
                "Please install the MS Core Fonts for the Web in whatever way makes sense on your system."
            )
            # very long term TODO: support other package managers

    #### Do the downloadables: ####

    def download_and_install(link, font, fontdir):
        # might need to spoof the user agent here
        with urllib.request.urlopen(link) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)

            fname = font.replace(" ", "_")
            if "Content-Disposition" in response.info():
                hh = cgi.parse_header(response.info()["Content-Disposition"])
                fname = os.path.splitext(hh[1]["filename"])[0]

            magic = subprocess.run(
                ["file", tmp_file.name], stdout=subprocess.PIPE, universal_newlines=True
            ).stdout.strip()
            printv(magic)

            for fmt in shutil.get_unpack_formats():
                printv(fmt)
                if fmt[0].lower() in magic.lower():
                    # think we'll need to unpack in place and then sudo mv
                    with tempfile.TemporaryDirectory() as tmpdir:
                        dirname = os.path.join(tmpdir, fname)
                        shutil.unpack_archive(tmp_file.name, dirname, fmt[0])
                        if fccachetry:
                            prompt(
                                "sudo mv "
                                + shlex.quote(dirname)
                                + " "
                                + shlex.quote(os.path.join(fontdir, fname))
                            )
                        elif sys.platform.startswith("darwin"):
                            os.system("open " + shlex.quote(dirname) + "/*.ttf")
                            os.system("open " + shlex.quote(dirname) + "/*.otf")
                        break
            else:
                if "font" in magic:
                    prompt(
                        "sudo mv "
                        + shlex.quote(tmp_file.name)
                        + " "
                        + shlex.quote(os.path.join(fontdir, fname))
                    )
                else:
                    printq("Could not figure out what to do! Skipping")
                    printq(link)

    ##### end download_and_install

    # figure out what we need

    # some downloads will supply us multiple fonts
    linkvals = {}
    for k, v in LINKS.items():
        for f in v:
            linkvals[f] = k

    # actually do things
    already_installed = []
    for font in listicle:
        printv(font)
        for linky, listy in LINKS.items():
            if match(font, listy) and (font not in already_installed):
                # actually download things
                download_and_install(linky, font, FONTDIR)
                already_installed.append(font)
                break
            else:
                continue
        else:
            printq(font, "is missing but could not be downloaded")

    printq(len(already_installed), "fonts installed (or at least downloaded):")
    for k in already_installed:
        printq("\t" + k)

    # update font cache
    if fccachetry:
        prompt("sudo fc-cache -f")
    else:
        printq(
            "The fonts could not be automatically installed but they have been downloaded to",
            FONTDIR,
        )
        printq("Please install the downloaded fonts manually.")


if __name__ == "__main__":
    main()
