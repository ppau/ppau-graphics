grep -hor "font-family[^;]*" Artwork | sort | uniq | cut -c 13- > FONTLIST.txt
