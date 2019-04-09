# THP2Epub
A modification of Emmanuel Gil Peyrot's THP2Epub script.

Originally from https://hg.linkmauve.fr/thp2epub/

Basically the same script, but with a couple of modifications to account for some changes to the THP site (SSL, tag layout, etc.)

It's a touhou-project.com downloader that scrapes posts from given threads.

# Features

* Has a GUI for easy use

* Title/Author search

* When the OP is an Anon, automatically only download posts that are over the mean length of all posts in the thread (currently very buggy and doesn't work half of the time, but after implementation it managed to reduce my epub for A Wizard is You from 6000 pages to 2000, so it must be doing *something*)

# Requirements

lxml

epub

tkinter

bs4

(oh and of course python3 but that should be obvious)

## Installing requirements

`pip install lxml`

`pip install epub`

`pip install bs4`

Download ActiveTcl from [here](https://www.activestate.com/products/activetcl/)- it contains Tkinter

# Usage: `python thp2epub.py`

There are a couple of issues with file closing that cause a PermissionError to show up, just find the temp file in %LOCALAPPDATA%\Temp and rename it to something with a .zip extension then unpack it to find the .xhtml files inside, which you can import into Calibre, convert to Epub then merge into one file using EpubMerge.

Any other complaints? Make an issue.
