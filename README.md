# ppau-graphics
Graphics for Pirate Party Australia.
(@ppau on GitHub.)

There are several purposes for this repository:

1. Version control and general ability for collaboration with source documents.
2. Build an infrastructure that allows us to seamlessly update authorisation tags and, if necessary, printing tags.

The system works by having the artist insert placeholder text, such as `PPAU_AUTH_TAG`, in the artworks instead of something like `Authorised by Name, Address`. The script will perform a textual find-and-replace and then render the artwork to a format more suitable for distribution, currently PNG and PDF.

# Requirements

The following programs are required by the render script.

- a working Python 3.5 (or newer) install to run it.
- `inkscape`
- `find(1)`
- `sed(1)`
- `grep(1)`
- `pdfunite`

If you do not specify a correct path to `inkscape`, the script will attempt to find it with `which(1)`.

`pdfunite` is usually installed as part of `poppler-tools`.

## Git LFS

**Most files in this repository are tracked using [Git LFS.](https://git-lfs.github.com/)** See the `.gitattributes` file for a detailed list. An example line:

`*.jpg filter=lfs diff=lfs merge=lfs -text`

Git LFS isn't usually installed by default. You'll need to run `git lfs install` *before* cloning. Otherwise most of the files will be broken.

## Fonts

You'll need the various fonts, too; at a minimum Open Sans (including Condensed) and Gehen Sans, although others might have been used. You can run `python3 list_fonts.py` to get a JSON of all the fonts used in the project and what files use them. This will be found in `FONTLIST.json`; it is recommended to run `list_fonts` yourself rather than relying on the JSON being up to date.


# Usage

To render the SVGs in the source directory, run the script `render.py` from the command line, probably with something like:

`python3 /path/to/render.py`

Add the help flag: `python3 /path/to/render.py --help` for a full list of options.

Replacement tags are specified in `auth_tag.txt` (authoriser) and `print_tag.txt` (printer).

There will be three variants of each file rendered:

1. with authorisation tag only (`*-auth.*`),
2. with both authorisation and printing tags (`*-both.*`),
3. with no tags (`*-none.*`)

Each variant will be rendered as a PNG and as a PDF. An SVG with text replacement corresponding to each type is also placed alongside.

So the single source `Artwork/marriage/cmon-aussie.svg` will result in the following files being generated:

- `Renders/marriage/cmon-aussie-auth.pdf`
- `Renders/marriage/cmon-aussie-auth.png`
- `Renders/marriage/cmon-aussie-auth.svg`
- `Renders/marriage/cmon-aussie-both.pdf`
- `Renders/marriage/cmon-aussie-both.png`
- `Renders/marriage/cmon-aussie-both.svg`
- `Renders/marriage/cmon-aussie-none.pdf`
- `Renders/marriage/cmon-aussie-none.png`
- `Renders/marriage/cmon-aussie-none.svg`

(If a print tag or an authorisation tag is omitted in a source file, corresponding files will not be rendered.)

## Kinds of tags

As of 2020, there are two levels of *authorisation* requirements, as well as *printer* identification requirements. 

Both kinds of authorisation tags require: 

* the name of the "disclosure entity" (e.g. "Pirate Party Australia")
* the name of the person authorising it (generally the current Secretary; first initial and last name suffice)

"Basic" requirements for PPAU comms apply generally to non-printed material such as :

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

SVG doesn't support multi-page documents, but it is now possible to collate SVGs into a PDF.  

## WSGI

There's a semi-experimental WSGI implementation in the subdirectory of that name.

Running `create_index.py` will generate you an `index.html` (which expects to be in the project root). It will also generate preview JPEGs which are much smaller than the PNGs.


# License

Artwork and text created by members of Pirate Party Australia is released under the Creative Commons [Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) license (CC-BY 4.0), unless otherwise specified.

Code created by members of Pirate Party Australia is released under the [Free Software Foundation General Public License, version 3](https://www.gnu.org/licenses/gpl-3.0.html), unless otherwise specified.

