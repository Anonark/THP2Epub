# THP2Epub
A touhou-project.com story downloader, modified from Emmanuel Gil Peyrot's THP2Epub script.

Download the latest version from [here](https://github.com/Anonark/THP2Epub/releases)

Originally from https://hg.linkmauve.fr/thp2epub/

It started out as basically the same script, but with a couple of modifications to account for some changes to the THP site (SSL, tag layout, etc.) Now, it's gotten enough features to become a full-fledged project of its own.

It's a touhou-project.com downloader that scrapes posts from given threads.

# Features

* Has a GUI for easy use

* Title/Author search

* Storylist caching

* Built-in library viewer where you can open downloaded files by doubleclicking

* When the OP is an Anon, automatically only download posts that are over the mean length of all posts in the thread (currently very buggy and doesn't work half of the time, but after implementation it managed to reduce my epub for Tenshi is in This Story from 1.3MB to 0.9MB, so it must be doing *something*)

# Requirements (Assuming you don't use the packaged version)

lxml

tkinter

bs4

(oh and of course python3 but that should be obvious)

## Installing requirements

`pip install lxml`

`pip install bs4`

Download ActiveTcl from [here](https://www.activestate.com/products/activetcl/)- it contains Tkinter

# Usage: `python thp2epub.py`

Any complaints? Make an issue.
