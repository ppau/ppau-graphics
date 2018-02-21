# CONTRIBUTING 

All contributed artwork should be in Scalable Vector Graphics (SVG) format. 

Please endeavour to follow the [Identity Style Guide](https://pirateparty.org.au/wiki/Identity_Style_Guide) where possible, especially for standalone artwork. 

Please go through the usual [Authorisation Processes](https://pirateparty.org.au/wiki/Authorisation_processes) too before uploading. There are already enough items in the unauthorised section!

If you must upload artwork that has not yet been authorised, ensure it goes to the unauthorised section and has a big red 'DRAFT' tag visible.

Artwork intended to be printed should avoid the use of partial transparency. 

Authorisation and Printing Tags need to be legible! As such, they should be no less than half the height of the next smallest piece of text in the artwork (typically the lower line in the party logo). Further, there needs to be sufficient contrast between the tag-text and the background. Setting the tag-text to be the same colour as the background, and then adjusting the brightness by 128 is a simple way to achieve this. 

In general, use Open Sans for general text and Open Sans Condensed for tag-text. 

If you use fonts other than those listed in the Identity Style Guide, run `python3 list_fonts.py` in the project root before committing. This will automatically update `FONTLIST.json`. Please only use fonts which are available under permissive licenses.

The Authorisation Tag placeholder is as follows (remove leading/trailing whitespace): 

    PPAU_AUTH_TAG
    
The Printing Tag placeholder is as follows (remove leading/trailing whitespace):

    PPAU_PRINT_TAG


