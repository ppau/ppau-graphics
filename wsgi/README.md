# README

# About/Setup

This folder contains a WSGI application intended for use with uWSGI (`myapp.py`), and the corresponding `myapp.ini` file.

You'll want to put these in a folder somewhere, `virtualenv` that folder (or even this one, provided it's not a horrendous security flaw), then install uWSGI in the virtualenv.
Then set up NGINX or whatever to look for uWSGI to respond to requests at your chosen URL, and make uWSGI run as a service.

# Requirements

Mostly as per the main script. The main additional requirements are uWSGI and NGINX.

Additionally, PDF merging is done with [PyPDF2](https://pythonhosted.org/PyPDF2/index.html) rather than `pdfunite`.
You can get that with `pip install pypdf2` inside the `virtualenv`.

# Notes:

As of 24th Feb 2018, PNG on-the-fly export is broken and I don't know why. PDF works fine and that was the main use-case anyway.

You probably need your virtualenv active when going `systemctl start myapp.service`...
