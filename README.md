# THP2Epub
A modification of Emmanuel Gil Peyrot's THP2Epub script.

Originally from https://hg.linkmauve.fr/thp2epub/

Basically the same script, but with a couple of modifications to account for some changes to the THP site (SSL, tag layout, etc.)

It's a touhou-project.com downloader that scrapes posts from given threads.

One of the key modifications I made is that it only downloads posts made by the OP by default, so no need to specify with -o.

# Requirements:

lxml

epub

(oh and of course python3 but that should be obvious)

## Installing requirements:

`pip install lxml`

`pip install epub`

# Usage: `python thp2epub.py -f FORUM_NAME LIST_OF_THREADS_SEPARATED_BY_SPACES`

Example: `python thp2epub.py -f sdm 166 442 739`

There are a couple of issues with file closing that cause a PermissionError to show up, just find the temp file in %LOCALAPPDATA%\Temp and rename it to something with a .zip extension then unpack it to find the .xhtml files inside, which you can import into Calibre, convert to Epub then merge into one file using EpubMerge.

There may be an issue with path names (specifically, backslashes vs. forward slashes) when running on Windows. In that case, just open an issue and I'll add a zipfile.py with the neccessary modifications.

Any other complaints? Make an issue.
