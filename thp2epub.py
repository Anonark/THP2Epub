#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
##
## Copyright © 2012 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
## Modifications & bug fixes provided by MKC 2019
##
## This program is free software; you can redistribute it and/or modify
## itoim under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##


from __future__ import unicode_literals

from lxml import etree
from lxml.builder import E
from time import strptime, strftime
from datetime import datetime
#from argparse import ArgumentParser

from functions import generate

import os
import sys

from tkinter import Tk, Entry, Text, IntVar, Checkbutton, Button, END, Menu


try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError


images_list = []
mime_type = {
    '.jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml'
}


class Thread(object):
    def __init__(self, op, replies):
        self.op = op
        self.replies = replies
        self.title = op.title
        if self.title is None:
            self.title = 'blank'
        self.author = op.author

    def render(self, only_op):
        html = E.html(
            E.head(
                E.title(self.title),
                E.link(href='story.css', type='text/css', rel='stylesheet') #TODO: convert it to a PI.
            ),
            E.body(
                E.h1(self.title)
            ),
            xmlns='http://www.w3.org/1999/xhtml'
        )

        body = html.find('body')
        body.append(self.op.render(display_title=False))
        #calc mean length of replies
        mean = (len(self.replies[0].content) + len(self.replies[-1].content)) / 2
        """for reply in self.replies:
            mean += len(reply.content)
        mean /= len(self.replies)"""

        for reply in self.replies:
            # Remove user answers if not wanted.
            if only_op and not reply.is_op(self.op):
                continue
            if (self.op.author.trip == None and self.op.author.name == None) and len(reply.content) < mean:
                continue

            body.append(reply.render())

        return html


class Post(object):
    def __init__(self, title, author, date, image, content):
        self.title = title
        self.author = author
        self.date = date
        self.image = image
        self.content = content

    def is_op(self, op):
        if self.author.trip is not None:
            return self.author.trip == op.author.trip
        elif self.author.name is not None:
            return self.author.name == op.author.name

    def render(self, display_title=True):
        if display_title:
            title = E.h2(self.title) if self.title and display_title else E.h2('⁂')
        else:
            title = ''

        img = self.image.render() if self.image else ''

        p = E.p()
        for item in self.content:
            #TODO: remove useless attributes like onclick.
            p.append(item)

        article = E.article(
            title,
            E.footer(
                E.cite(self.author.render()),
                ' ',
                E.time(strftime('%y/%m/%d(%a)%H:%M', self.date), time=strftime('%y-%m-%dT%H:%M:%SZ', self.date))
            ),
            img,
            p
        )
        return article


class Image(object):
    def __init__(self, name, filesize, size, url):
        self.name = name
        self.filesize = filesize
        self.size = size
        self.url = url

    def render(self):
        try:
            url_file = urlopen("https://www.touhou-project.com"+self.url)
        except HTTPError:
            return ''
        try:
            with open(self.name, 'wb') as out:
                out.write(url_file.read())
        except:
            return ''
        images_list.append(self.name)
        return E.img(src=self.name, alt=self.name)


class Author(object):
    def __init__(self, name, trip, mail):
        self.name = name
        self.trip = trip
        self.mail = mail

    def render(self):
        if self.name is not None or self.trip is not None:
            return '{}{}'.format(self.name, self.trip)
        else:
            return 'Anonymous'

def gettag(tree, tag):
    # dfs to find 'label', 'blockquote', etc.
    found = None
    for temp in tree:
        if temp.tag == tag:
            return temp
        found = gettag(temp, tag)
        if found is not None and found.tag == tag:
            break
    return found


def parse_post(root):
    # We use the filesize element because it contains the image name.
    label = root.find('label')
    filesize = root.find('span[@class="filesize"]')
    if filesize is not None:
        a = filesize.getnext().getnext()
        filesize = etree.tostring(filesize, method='text', encoding='UTF-8')
        filesize = filesize.split()
        name = filesize[7:-2]
        name = b' '.join(name)
        try:
            name = name.decode('UTF-8')
        except UnicodeDecodeError:
            for i in range(-5, -42, -1):
                char = name[i] if type(name[i]) is int else ord(name[i])
                if char & 0xc0 == 0xc0:
                    name = name[:i-1] + b'\xef\xbf\xbd' + name[-4:]
                    break
            name = name.decode('UTF-8')
        filesize, size = filesize[3][1:], filesize[5]
        if a.tag == 'a':
            url = a.get('href')
        else:
            url = a.find('img').get('src')

        image = Image(name, filesize, size, url)
    else:
        image = None

    #label = root.find('label')
    label = gettag(root, 'label')
    """if label is None:
        label = root.find('div[@class="post originalpost"]')
        if label is not None:
            label = root.find('div[@class="post originalpost"]').find('label')
        else:
            label = root.find('div[@class="post originalpost knavanchor"]')
            if label is not None:
                label = root.find('div[@class="post originalpost knavanchor"]').find('label')
            else:
                label = root.find('div[@class="originalpost post"]').find('label')
    """
    title = label.find('span[@class="filetitle"]')
    title = title.text.strip() if title is not None else None
    name = label.find('span[@class="postername"]')
    if name is not None:
        last = name
        a = name.find('a')
        if a is not None:
            mail = a.get('href')
            name = a.text
        else:
            mail = ''
            name = name.text
    else:
        mail = ''
        name = ''

    postertrip = label.find('span[@class="postertrip"]')
    if postertrip is not None:
        trip = postertrip.text
        last = postertrip
    else:
        trip = ''

    author = Author(name, trip, mail)
    try:
        date = strptime(last.tail.strip(), '%y/%m/%d(%a)%H:%M')
    except:
        date = datetime(2019, 1, 1, 0, 0).timetuple()

    #blockquote = root.find('blockquote')
    blockquote = gettag(root, 'blockquote')
    """if blockquote is None:
        blockquote = root.find('div[@class="post originalpost"]')
        if blockquote is None:
            blockquote = root.find('div[@class="post originalpost knavanchor"]').find('blockquote')
        else:
            blockquote = root.find('div[@class="post originalpost"]').find('blockquote')
    """
    content = []
    for item in blockquote:
        if item is str and item.strip() == '':
            continue
        content.append(item)

    return Post(title, author, date, image, content)


def parse_thread(url, consoletext):
    consoletext.insert(END, 'URL of thread: '+url+'\n')
    consoletext.insert(END, 'Parsing thread...\n')
    try:
        tree = etree.parse(urlopen(url), etree.HTMLParser())
        """root = tree.find('//form[@id="delform"]')
        if root is None:
            root = tree.find('//div[@class="originalpost post"]')
            if root is None or root.find('blockquote') is None:
                root = tree.find('//body')"""
        root = tree.find('//body')
        op = parse_post(root)
    
        replies = []
        td = root.findall('.//td[@class="reply"]')
        for reply in td:
            replies.append(parse_post(reply))
            
            
        consoletext.insert(END, 'Finished parsing thread!\n')
        return Thread(op, replies)
    except HTTPError:
        consoletext.insert(END, 'Thread not found!\n')
        return

def main(url, forum, only_op, threads, consoletext):
    consoletext.delete(1.0,END)
    try:
        threads = [int(i) for i in threads]
    except:
        consoletext.insert(END, 'Invalid characters found in thread list!')
        return
    threads_list = []
    for thread in threads:
        consoletext.insert(END, 'Rendering of thread №{}…\n'.format(thread))
        t = parse_thread(url.format(forum, thread), consoletext)
        threads_list.append(t)

        html = t.render(only_op)

        # Use b mode as it allows us to directly dump UTF-8 data.
        consoletext.insert(END, 'Downloaded thread №{}, generating XHTML...\n'.format(thread))
        with open('{}.xhtml'.format(thread), 'wb') as f:
            f.write(etree.tostring(html, pretty_print=True, xml_declaration=True, doctype='<!DOCTYPE html SYSTEM "/tmp/test.dtd">', encoding='UTF-8'))

    consoletext.insert(END, 'Finished downloading threads! Now generating Epub...\n')

    #book = epub.EpubBook()
    #with epub.open(threads_list[0].title+'.epub', 'w') as book:
    t = threads_list[0]
    
    """book.set_identifier(t.title+str(threads[0]))
    book.set_title(t.title)
    book.add_author(t.author.render())
    #book.set_date(strftime('%y-%m-%dT%H:%M:%SZ'))
    book.set_language('en')"""
    list_chaps = []
    for thread in threads:
        
        filename = '{}.xhtml'.format(thread)
        list_chaps.append(filename)
        """
        #manifest_item = epub.opf.ManifestItem(identifier='thread_{}'.format(thread),
        #                                      href=filename,
        #                                      media_type='application/xhtml+xml')
        chap = epub.EpubHtml(title = threads_list[threads.index(thread)].title, file_name = 'chap'+filename, lang='en')
        #print(chap.get_body_content())
        #print('\n'.join(open(filename, encoding='utf-8').readlines()))
        chap.set_content('\n'.join(open(filename, encoding='utf-8').readlines()));
        list_chaps.append(chap)
        book.add_item(chap)"""

    """for image in images_list:
        extension = image[-4:]
        manifest_item = epub.opf.ManifestItem(identifier='image_{}'.format(image),
                                              href=image,
                                              media_type=mime_type[extension])
        book.add_item(image, manifest_item, True)"""

    """css_style = epub.EpubItem(uid='style',
                                          file_name='nav.css',
                                          media_type='text/css', content = '\n'.join(open('story.css', encoding='utf-8').readlines()))
    book.add_item(css_style)
    book.spine = list_chaps

    #book.toc.title = t.title
    #nav_map = book.toc.nav_map
    nav_points = []
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    """"""for thread in threads:
        nav_point = epub.ncx.NavPoint()
        nav_point.identifier = 'thread_%d' % thread
        nav_point.add_label('Thread №%d' % thread)
        nav_point.src = '%d.xhtml' % thread
        nav_points.append(nav_point)
        
    
    nav_map.nav_point + nav_points"""
    #epub.write_epub(threads_list[0].title+'.epub', book)
    generate(list_chaps, t.title, t.author.render(), "1", str(len(list_chaps)))
    consoletext.insert(END, 'Finished all operations! The story has been saved as ' + t.title + "_" + "1" + "-" + str(len(list_chaps)) + ".epub")


def restart():
    os.execl(sys.executable, sys.executable, * sys.argv)

if __name__ == '__main__':
    # do GUI
    mainwindow = Tk()
    mainwindow.title('THP2Epub')
    #write widgets
    #restart button
    filemenu = Menu(mainwindow)
    filemenu.add_command(label="Restart Program", command=restart)
    mainwindow.config(menu=filemenu)
    
    #show console log
    consolelog = Text(mainwindow)
    consolelog.pack()
    #get forum name
    forum = Entry(mainwindow)
    forum.insert(END, 'Forum Name (EX: sdm)')
    forum.pack()
    
    #get thread ids (title search coming soon)
    story = Entry(mainwindow)
    story.insert(END, 'Thread IDs (EX: 142 255 2736)')
    story.pack()
    
    #only get op posts?
    onlyop = IntVar()
    Checkbutton(mainwindow, text="Download only OP posts?", variable=onlyop).pack()
    
    #download button
    downloadbutton = Button(mainwindow, text='Download', command=lambda: main('https://www.touhou-project.com/{}/res/{}.html', forum.get(), True if onlyop.get() == 1 else False, story.get().split(), consolelog))
    downloadbutton.pack()
    
    mainwindow.mainloop()
    """parser = ArgumentParser(description='Download and convert THP stories.')

    parser.add_argument('threads', metavar='THREADS', nargs='+', type=int, help='List of the threads of the story.')
    parser.add_argument('-u', '--url', metavar='URL', default='https://www.touhou-project.com/{}/res/{}.html', help='URL pattern from which the story will be downloaded, with the first {} as the forum, and the second as the thread.')
    parser.add_argument('-f', '--forum', metavar='FORUM', default='sdm', help='The name of the forum (example: sdm, th, etc.).')
    parser.add_argument('-o', '--only-op', action='store_true', help='Include only posts made by the original poster.')

    args = parser.parse_args()

    main(args.url, args.forum, args.only_op, args.threads)"""
