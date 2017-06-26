# ppau-graphics
Graphics for @ppau


There are several purposes for this repository:

1. Version control and general ability for collaboration with source documents.
2. Build an infrastructure that allows us to seamlessly update authorisation tags and, if necessary, printing tags.

The system works by inserting placeholder text, such as `PPAU_AUTH_TAG`, in the artworks instead of something like `Authorised by Name, Address`. The script will perform a textual find-and-replace and then render the artwork to a format more suitable for distribution. 

# Requirements 

The following programs are required by the render script. 

- a working Python 3.5 (or newer) install to run it. 
- `rsvg-convert` (path defined in the script, you'll probably have to update this) 
- `find(1)` 
- `sed(1)` 

Additionally, most files in this repository are tracked using Git LFS. See the `.gitattributes` file for a detailed list. An example line: 

`*.jpg filter=lfs diff=lfs merge=lfs -text` 

The `rsvg-convert` tool is installed as part of `librsvg` on my machine. 

# Usage 

To render the SVGs to PDF, run the script `render.py` from the command line, probably with something like: 

`python3 /path/to/render.py` 

Add the help flag: `python3 /path/to/render.py --help` for a list of options. 

Replacement tags are specified in `auth_tag.txt` (authoriser) and `print_tag.txt` (printer). 

## Examples 

To render the artworks as PNGs rather than PDF, we'd use the following:

`python3 /path/to/render.py --output_format png` 

To temporarily override the placeholder authorisation tag text: 

`python3 /path/to/render.py --auth_tag AUTHORISED_BY_CTHULHU`

Be careful using the `--auth_tag` and `--print_tag` flags: remember that they define the text that is to be *replaced*. Specifying an empty string, or something that resembles SVG, will cause issues. 

To not print any tags (equivalent to making `auth_tag.txt` and `print_tag.txt` empty files): 

`python3 /path/to/render.py --no_tags` 

