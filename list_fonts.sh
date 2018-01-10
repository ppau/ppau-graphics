grep -Eorh -e "font-family(:|=)'[^']*'" -e 'font-family(:|=)"[^"]*"' -e "font-family(:|=)[^;>']*" -e 'font-family(:|=)[^;>"]*'  Artwork | sort | uniq | cut -c 13- > FONTLIST.txt

#