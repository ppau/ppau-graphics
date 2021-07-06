# ppau-graphics
Graphics for Pirate Party Australia.
(@ppau on GitHub.)

There are several purposes for this repository:

1. Version control and general ability for collaboration with source documents.
2. Build an infrastructure that allows us to seamlessly update authorisation tags and, if necessary, printing tags.
3. ... and in turn, permit self-serve poster generation with appropriate tags. 

The system works by having the artist insert placeholder text, such as `PPAU_AUTH_TAG`, in the artworks instead of something like `Authorised by Name, Address`. The script will perform a textual find-and-replace and then render the artwork to a format more suitable for distribution, currently PNG and PDF.

## Ubuntu/Debian quickstart (recent releases)

    sudo apt-get install python3 git-lfs inkscape imagemagick poppler-utils fontconfig
    git clone https://github.com/ppau/ppau-graphics.git && cd ppau-graphics
    ./font-installer.py
    nano print_tag.txt
    ./render.py

If running on a server with WSGI you can leave `print_tag.txt` as is.

# Requirements

The following programs are required by the render script.

- a working Python 3.5 (or newer) install to run it.
- Inkscape **(version 1.0 required)**
- `find(1)`
- `sed(1)`
- `grep(1)`
- `pdfunite`
- `pngcrush` (optional)

If you do not specify a correct path to `inkscape`, `pdunite` or `pngcrush`, the script will attempt to find it with `which(1)`.

`pdfunite` is usually installed as part of `poppler-utils` or `poppler-tools`.

`find`, `sed` and `grep` should be installed by default on any POSIX system, but may be missing on Windows. 

## Git LFS

**Most files (in particular, the SVG artwork source files) in this repository are tracked using [Git LFS.](https://git-lfs.github.com/)** See the `.gitattributes` file for a detailed list. An example line:

`*.jpg filter=lfs diff=lfs merge=lfs -text`

Git LFS isn't usually installed by default. You'll likely need to run `git lfs install` *before* cloning - consider doing it even if your package manager has it installed. Otherwise most of the files will be broken.

## Fonts

You'll need the various fonts, too; at a minimum Open Sans (including Condensed) and Gehen Sans, although others might have been used. You can run `python3 list_fonts.py` to get a JSON of all the fonts used in the project and what files use them. This will be found in `FONTLIST.json`; it is recommended to run `list_fonts` yourself rather than relying on the JSON being up to date.

Run `font_installer.py` to attempt to install fonts automatically, or refer to CONTRIBUTING.md for a a fairly comprehensive list of download links. 

# Usage

To render the SVGs in the source directory, run the script `render.py` from the command line, perhaps with something like:

    python3 /path/to/render.py

Add the help flag: `python3 /path/to/render.py --help` for a full list of options.

Replacement tags are specified in `auth_tag.txt` and `auth_tag_basic.txt` (authoriser) and `print_tag.txt` (printer).

There will be three possible variants of each file rendered:

1. with authorisation tag only (`*-auth.*`),
2. with both authorisation and printing tags (`*-both.*`),
3. with no tags (`*-none.*`) if the source file doesn't provide for them.

Each variant will be rendered as a PNG for digital use and as a PDF for printing. An SVG with text replacement corresponding to each type is also placed alongside.

So the single source `Artwork/youtube/youtube.svg` will result in the following files being generated:

- `Renders/youtube/youtube-auth.png`
- `Renders/youtube/youtube-auth.svg`
- `Renders/youtube/youtube-both.pdf`
- `Renders/youtube/youtube-both.svg`

## Kinds of tags

As of 2020, there are two levels of *authorisation* requirements, as well as *printer* identification requirements. 

Both kinds of authorisation tags require: 

* the name of the "disclosure entity" (e.g. "Pirate Party Australia")
* the name of the person authorising it (generally the current Secretary; first initial and last name suffice)

"Basic" requirements for PPAU communications apply generally to non-printed material such as :

* the *town or city* of the disclosure entity, or else the town or city of the authorising person

"Full" requirements generally apply to physical material such as posters, stickers or how-to-vote cards: 

* the *full street address* or the disclosure entity, or else one where the authorising person can be contacted

There's only one kind of printer tag:

* The name of the printer (or more likely, company name)
* The full street address of the printer (it might be necessary in some cases to use head-office location)

The render script will by default output the basic auth tag in auth-only files, and the full auth tag in files that also contain a print tag. 

## Examples

To temporarily override the placeholder authorisation tag text:

`python3 /path/to/render.py --auth_tag AUTHORISED_BY_CTHULHU`

Be careful using the `--auth_tag` and `--print_tag` flags: remember that they define the text that is to be *replaced*. Specifying an empty string, or something that resembles SVG, will cause issues.

To specify an alternate file containing the authorisation tag:

`python3 /path/to/render.py --auth_tag_file /path/to/file`

## Multi-page documents

SVG doesn't support multi-page documents, but it is now possible to collate SVGs into a PDF (this is why `pdfunite` is needed). 

This is done by a file naming convention: `foo/bar_p1.svg`, `foo/bar_p2.svg`, `foo/bar_p3.svg` will all be collated as `foo/bar.pdf`. Numbers are handled correctly (`11` comes after `2`) and missing pages are simply skipped.

The exact format used is the regex `(.*)(_[pP])(\d+)(-\w*)?$` where the first group is the name, the second group marks a page number, the third group is the digits of the page number, and the fourth group is an optional variant descriptor, e.g. "light" or "dark". Any file extension is stripped before the regex is matched. You may pass in a different regex with `--collate-fmt` but the groups will of course be interpreted the same way, so the only change advised is to group 2. 

## Crushing PNGs

`pngcrush` is optional with `--crush`; crushing PNGs at time of writing shows an average saving of 15% size, and (on author's machine) takes about 5 seconds per image updated. Disk space is pretty cheap and plentiful these days, so crushing is off by default. 

A log of timestamps between which rendered files have been crushed is kept in `Renders/.crush_timestamps.tsv`. If you only sometimes crush PNGs you may be able to use this information 

## WSGI and servers

There's a semi-experimental WSGI implementation in the subdirectory of that name powering self-serve PDF generation. 

Running `create_index.py` will generate you an `index.html` (which expects to be in the project root). It will also generate preview JPEGs which are much smaller than the PNGs, using ImageMagick's `convert`.

`update.sh` is designed to be run automatically on machines that don't edit the repository. It will perform a `git pull`, remove any deleted artwork's renders, render new/changed artwork and create `index.html`. 

It takes several arguments: 
- the "site root" (e.g. `https://example.com/ppau-graphics`) is required; 
- whether to crush PNGs (`--crush`)
- the path to a log file (`--log /path/to/file`). 

N.B. this is changed from the previous behaviour as of 2021-07-06.

# License

Artwork and text created by members of Pirate Party Australia is released under the Creative Commons [Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) license (CC-BY 4.0), unless otherwise specified.

Code created by members of Pirate Party Australia is released under the [Free Software Foundation General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html), unless otherwise specified.

