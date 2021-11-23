#!/usr/bin/env python3

################################################################################
#### ABOUT:                                                                 ####
#### Get unique fontnames out of the SVGs in the artwork directory.         ####
#### The names will be placed in a file.
################################################################################


def main():
    SOURCE_DIR = "Artwork"  # default: "Artwork"
    OUTPUT_FILE = "FONTLIST.json"  # default: "FONTLIST.json"

    EXCLUDE = {"sans-serif"}  # not an actual font

    ################################################################################
    #### You shouldn't need to ever edit anything below this comment.           ####
    ################################################################################

    VERSION = "0.0.4"

    import subprocess
    import argparse
    import re
    import json
    import sys

    # Parse Arguments

    parser = argparse.ArgumentParser(
        description="Collate the fonts used.", prog="PPAU-Graphics Font Lister"
    )

    parser.add_argument(
        "-s",
        "--source_dir",
        dest="source_dir",
        action="store",
        default=SOURCE_DIR,
        help="the directory containing the source files",
    )

    parser.add_argument(
        "-o",
        "--output_file",
        dest="output_file",
        action="store",
        default=OUTPUT_FILE,
        help="the file listing the font families",
    )

    parser.add_argument(
        "-i",
        "--invert",
        dest="invert",
        action="store_const",
        default=False,
        const=True,
        help="output an inverted file too, indexed by font",
    )

    parser.add_argument(
        "-l",
        "--list",
        dest="list_too",
        action="store_const",
        default=False,
        const=True,
        help="also list all font families used, to standard output",
    )

    parser.add_argument(
        "-m",
        "--missing",
        dest="show_missing",
        action="store_const",
        default=False,
        const=True,
        help="list missing font families instead",
    )

    parser.add_argument(
        "-u",
        "--unusual",
        dest="unusual",
        nargs="?",
        const=5,
        type=int,
        metavar="MAX",
        help="list font families used by only a few files instead",
    )

    parser.add_argument("--version", action="version", version="%(prog)s " + VERSION)

    arguments = parser.parse_args()

    # Update Flags

    SOURCE_DIR = arguments.source_dir
    OUTPUT_FILE = arguments.output_file

    combo = {}
    allnames = {}

    pattern = re.compile(r"font-family(:|=)['\"]?([^;>'\"]*)")

    # Recursively find all SVGs in SOURCE_DIR
    SVGs = (
        subprocess.run(
            ["find", SOURCE_DIR, "-type", "f", "-name", "*.svg"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )
        .stdout.strip()
        .split(sep="\n")
    )

    for s in SVGs:
        if len(s) == 0:
            continue

        results = set([])

        with open(s, "r", encoding="utf-8") as s_file:

            for line in s_file:
                match = pattern.search(line)
                if match:
                    stripped = match.group(2).strip().strip('"').strip("'").strip()
                    if stripped and stripped not in EXCLUDE:
                        results.add(stripped)
        if len(results):
            combo[s] = results

            for n in results:
                if n not in allnames:
                    allnames[n] = [s]
                else:
                    allnames[n] += [s]

    listnames = sorted(list(allnames))

    with open(arguments.output_file, "w") as fontlist_file:
        # pretty print

        keys = sorted(combo.keys())

        allfonts = [{"all": listnames}]
        tree = [{i: list(combo[i])} for i in keys]
        print(json.dumps(allfonts + tree), file=fontlist_file)

    if arguments.invert:
        ofbits = arguments.output_file.split(".")
        invname = ".".join(ofbits[:-1]) + "_inverted." + ofbits[-1]
        with open(invname, "w") as inv_file:
            print(json.dumps(allnames), file=inv_file)

    ### The fancy listing ###
    if arguments.list_too and not (arguments.show_missing or arguments.unusual):
        print(*listnames, sep="\n")

    elif arguments.unusual and not arguments.show_missing:
        for k, v in allnames.items():
            if len(v) <= arguments.unusual:
                print(k, " [", len(v), "]" "\n\t", "\n\t".join(v), sep="")

    elif arguments.show_missing:
        installed_fonts = None

        fcl_try = subprocess.run(
            ["which", "fc-list"], stdout=subprocess.PIPE, universal_newlines=True
        ).stdout.strip()

        if fcl_try:
            installed_fonts = set(
                subprocess.run(
                    [fcl_try, ":", "family"],
                    stdout=subprocess.PIPE,
                    universal_newlines=True,
                )
                .stdout.strip()
                .split(sep="\n")
            )
        elif sys.platform == "darwin":
            installed_fonts = subprocess.run(
                ["system_profiler", "SPFontsDataType"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
            ).stdout.strip()
        else:
            print(
                "ERROR: Could not list system fonts. (Windows is currently not supported.)"
            )
            exit(1)

        for font in listnames:
            if font not in installed_fonts:
                if arguments.unusual:  # basically embedded 'unusual' in 'missing'
                    if len(allnames[font]) > arguments.unusual:
                        continue
                    else:
                        print(
                            font,
                            " [",
                            len(allnames[font]),
                            "]" "\n\t",
                            "\n\t".join(allnames[font]),
                            sep="",
                        )
                else:
                    print(font)


if __name__ == "__main__":
    main()
