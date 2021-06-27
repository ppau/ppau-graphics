# README - WSGI

This folder contains a WSGI application intended for use with uWSGI (`ppaugraphics.py`), and corresponding configuration files. 

The script assumes the presence of a copy of this repository in the static website serve path `/var/www/SITE_NAME.tld/html/FOO`, such that 
- `https://SITE_NAME.tld/FOO/index.html` is where the requests come from
- `/var/www/SITE_NAME.tld/html/FOO/Artwork` is the artwork source directory, 
- `/var/www/SITE_NAME.tld/html/FOO/MANIFEST.json` is the manifest, and 
- `/var/www/SITE_NAME.tld/html/FOO/auth_tag.txt` is the auth tag 

## Setup (for recent Debian/Ubuntu)

Ensure the existence of all needed packages (note that PyPDF2 is used here, rather than pdfunite as in the main script):

    sudo apt-get install nginx uwsgi python3-pypdf2

(N.B.: I tried using a `virtualenv` and it was a bit of a mess, so everything is system-installed.)

Create a service directory:

    sudo mkdir /etc/ppaugraphics

Copy the WSGI-related files from this subdirectory of the repository to the service directory:

    sudo cp -r /PATH/TO/ppau-graphics/wsgi/* /etc/ppaugraphics
    
In your NGINX config you'll need the following:

	location /FOO/wsgi {
		include uwsgi_params;
		uwsgi_pass unix:///run/uwsgi/ppaugraphics.sock;
	}

[`/FOO` should be as above. It also might not exist, in which case you'd just have `https://SITE_NAME.tld/index.html` and `location /wsgi {`, etc.]

Don't forget to test your configuration with `sudo nginx -t`

Copy the `ppaugraphics.service.conf` where it needs to be, then edit if required:

    sudo cp /etc/ppaugraphics/ppaugraphics.service.conf /etc/systemd/system/ppaugraphics.service
    sudo nano /etc/systemd/system/ppaugraphics.service
    
Enable and activate:
    
    sudo systemctl enable --now ppaugraphics
    sudo systemctl reload nginx
    
