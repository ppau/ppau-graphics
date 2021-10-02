#!/bin/bash

# PPAU Graphics Update Script
USAGE="update.sh [--crush] [--fonts] [--log log_file] <site_address>"

# Handle arguments
CRUSH=""
INSTALLFONTS="N"
LOGGING="--quiet"
ROOT="."
OTHERS=()

# gotta be at least one argument
if [[ $# -ne 2 ]]; then
    echo "Usage: $USAGE"
    exit
fi

for arg in "$@"
do
    case $arg in
        -h|--help)
        echo "Usage: $USAGE"
        exit
        ;;
        --crush)
        CRUSH="--crush"
        shift
        ;;
        --fonts)
        INSTALLFONTS="Y"
        shift
        ;;
        --log)
        LOGGING="--log $2"
        shift
        shift
        ;;
        *)
        OTHERS+=("$1")
        shift
        ;;
    esac
done

ROOT="$OTHERS" # by default, the first?

# gotta do this
cd $(dirname "$0")

# pull and render
git reset --hard --quiet
git pull --quiet

if [ "$INSTALLFONTS" == "Y" ]
then
    python3 font-installer.py $LOGGING
fi

python3 clean.py $LOGGING
python3 render.py $LOGGING $CRUSH
python3 create_index.py --site-root $ROOT $LOGGING
cd Logos
if [[ "$ROOT" != "." ]]; then
    python3 RenderLogos.py --page-root "$ROOT/Logos" $LOGGING
else
    python3 RenderLogos.py --page-root "." $LOGGING
fi