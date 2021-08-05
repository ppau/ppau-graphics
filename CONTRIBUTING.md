# CONTRIBUTING 

All contributed artwork should be in Scalable Vector Graphics (SVG) format. 

Please endeavour to follow the [Identity Style Guide](https://pirateparty.org.au/wiki/Identity_Style_Guide) where possible, especially for standalone artwork. 

Please go through the usual [Authorisation Processes](https://pirateparty.org.au/wiki/Authorisation_processes) too before uploading. There are already enough items in the unauthorised section!

If you must upload artwork that has not yet been authorised, ensure it goes to the unauthorised section and has a big red 'DRAFT' tag visible.

Artwork intended to be printed should avoid the use of partial transparency. 

Authorisation and Printing Tags need to be legible! (The law is that they must have a font size that can be read by someone with 20/20 vision.) As such, tags should be no less than half the height of the next smallest piece of text in the artwork (typically the lower line in the party logo). Further, there needs to be sufficient contrast between the tag-text and the background. Setting the tag-text to be the same colour as the background, and then adjusting the brightness by 128 is a simple way to achieve this. 

In general, use Open Sans for general text and Open Sans Condensed for tag-text. 

If you use fonts other than those listed in the Identity Style Guide, run `python3 list_fonts.py` in the project root before committing. This will automatically update `FONTLIST.json`. Please only use fonts which are available under permissive licenses, and add their download links to the list below...

The Authorisation Tag placeholder is as follows (remove leading/trailing whitespace): 

    PPAU_AUTH_TAG
    
The Printing Tag placeholder is as follows (remove leading/trailing whitespace):

    PPAU_PRINT_TAG


# Font Sources 

You will need these fonts at a minimum:

* [Gehen Sans](https://github.com/ppau/gehen-fonts/raw/gh-pages/gehen-sans-otf-0.4.tar.gz)
* [Open Sans](https://fonts.google.com/download?family=Open%20Sans), including [Condensed](https://fonts.google.com/download?family=Open%20Sans%20Condensed)
* [Fira Sans, all widths](https://bboxtype.com/downloads/Fira/Download_Folder_FiraSans_4301.zip)
* The various Microsoft Core Fonts (Arial, Courier New, etc.) Preinstalled on Windows and Mac, try the `ttf-mscorefonts-installer` on Debian-like systems. 
* [VIDEO PIRATE](https://www.ffonts.net/VIDEO-PIRATE.font.zip)
* [Jost*](https://indestructibletype.com/Jost.zip)
* [Liberation fonts](https://github.com/liberationfonts/liberation-fonts/files/4743886/liberation-fonts-ttf-2.1.1.tar.gz)
* [DejaVu fonts](http://sourceforge.net/projects/dejavu/files/dejavu/2.37/dejavu-fonts-ttf-2.37.zip)

And these fonts on occasion:

* [Airstream](https://dl.dafont.com/dl/?f=airstream)
* [Deftone Stylus](https://dl.dafont.com/dl/?f=deftone_stylus)
* [Minecraft](https://dl.dafont.com/dl/?f=minecraft)
* [Roboto Slab](https://fonts.google.com/download?family=Roboto%20Slab)
* [Showtime](https://dl.dafont.com/dl/?f=showtime)
* [Source Serif Pro](https://github.com/adobe-fonts/source-serif-pro/releases/download/3.001R/source-serif-pro-3.001R.zip)
* [Lazer84](https://dl.dafont.com/dl/?f=lazer84)


If it's in `__Unauthorised` don't worry about it too much. 

If you're on Linux or Mac, you should be able to run 
    
    python3 list_fonts.py --missing
    
For a list of font families that are referenced by one or more files, but that you don't have installed on your system. This works regardless of how up-to-date the list above is!

You might also find `--invert` to be useful if you're trying to figure out which files use a particular font, e.g. if you're trying to replace said font. 

    python3 list_fonts.py --invert
    
Further, there's `python3 font_installer.py` which does as much of this automatically as possible. But it has to be manually kept up-to-date with the list above. 



