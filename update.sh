#!/bin/bash

# PPAU Graphics Update Script
# Usage: ./update.sh <site_address> [log_file]

# this has to be first lol
cd $(dirname "$0")

# pull and render
git reset --hard --quiet
git pull --quiet

if [[ $# -eq 1 ]]; then
    python3 clean.py --quiet
    python3 render.py --no-print --quiet
    python3 create_index.py --site-root "$1" --quiet
    cd Logos
    if [[ "$1" != "." ]]; then
        python3 RenderLogos.py --page-root "$1/Logos" --quiet
    else
        python3 RenderLogos.py --page-root "." --quiet
    fi
elif [[ $# -eq 2 ]]; then
    python3 clean.py --log "$2"
    python3 render.py --no-print --log "$2"
    python3 create_index.py --site-root "$1" --log "$2"
    cd Logos
    if [[ "$1" != "." ]]; then
        python3 RenderLogos.py --page-root "$1/Logos" --log "$2"
    else
        python3 RenderLogos.py --page-root "." --log "$2"
    fi
else 
    echo "Missing argument: <site_address>"
fi

