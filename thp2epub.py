#!/usr/bin/env python
# -*- encoding: UTF-8 -*-
##
## Copyright © 2012 Emmanuel Gil Peyrot <linkmauve@linkmauve.fr>
## Modifications & bug fixes provided by MKC 2019
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 3 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##


from __future__ import unicode_literals

from lxml import etree
from lxml import html
from lxml.builder import E
from time import strptime, strftime
from datetime import datetime
import epub
from argparse import ArgumentParser

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

        for reply in self.replies:
            # Remove user answers if not wanted.
            if not reply.is_op(self.op):
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
        return self.author.trip == op.author.trip

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
        return '{}{}'.format(self.name, self.trip)


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

    label = root.find('label')
    if label is None:
        label = root.find('div[@class="post originalpost"]')
        if label is None:
            label = root.find('div[@class="post originalpost knavanchor"]').find('label')
        else:
            label = root.find('div[@class="post originalpost"]').find('label')
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

    blockquote = root.find('blockquote')
    if blockquote is None:
        blockquote = root.find('div[@class="post originalpost"]')
        if blockquote is None:
            blockquote = root.find('div[@class="post originalpost knavanchor"]').find('blockquote')
        else:
            blockquote = root.find('div[@class="post originalpost"]').find('blockquote')
    content = []
    for item in blockquote:
        if item is str and item.strip() == '':
            continue
        content.append(item)

    return Post(title, author, date, image, content)


def parse_thread(url):
    tree = etree.parse(urlopen(url), etree.HTMLParser())

    root = tree.find('//form[@id="delform"]')
    if root is None:
        root = tree.find('//div[@class="originalpost post"]')
        if root is None:
            root = tree.find('//body')
    op = parse_post(root)

    replies = []
    td = root.findall('.//td[@class="reply"]')
    for reply in td:
        replies.append(parse_post(reply))

    return Thread(op, replies)


def main(url, forum, only_op, threads):
    threads_list = []
    for thread in threads:
        print('Rendering of thread №{}…'.format(thread))
        t = parse_thread(url.format(forum, thread))
        threads_list.append(t)

        html = t.render(only_op)

        # Use b mode as it allows us to directly dump UTF-8 data.
        with open('{}.xhtml'.format(thread), 'wb') as f:
            f.write(etree.tostring(html, pretty_print=True, xml_declaration=True, doctype='<!DOCTYPE html SYSTEM "/tmp/test.dtd">', encoding='UTF-8'))


    with epub.open('story.epub', 'w') as book:
        t = threads_list[0]

        book.opf.metadata.add_title(t.title)
        book.opf.metadata.add_creator(t.author.render())
        book.opf.metadata.add_date(strftime('%y-%m-%dT%H:%M:%SZ'))
        book.opf.metadata.add_language('en')

        for thread in threads:
            filename = '{}.xhtml'.format(thread)
            manifest_item = epub.opf.ManifestItem(identifier='thread_{}'.format(thread),
                                                  href=filename,
                                                  media_type='application/xhtml+xml')
            book.add_item(filename, manifest_item, True)

        for image in images_list:
            extension = image[-4:]
            manifest_item = epub.opf.ManifestItem(identifier='image_{}'.format(image),
                                                  href=image,
                                                  media_type=mime_type[extension])
            book.add_item(image, manifest_item, True)

        manifest_item = epub.opf.ManifestItem(identifier='style',
                                              href='story.css',
                                              media_type='text/css')
        book.add_item('story.css', manifest_item)

        book.toc.title = t.title
        nav_map = book.toc.nav_map
        for thread in threads:
            nav_point = epub.ncx.NavPoint()
            nav_point.identifier = 'thread_%d' % thread
            nav_point.add_label('Thread №%d' % thread)
            nav_point.src = '%d.xhtml' % thread
            nav_map.nav_point.append(nav_point)
        book.close()


if __name__ == '__main__':
    parser = ArgumentParser(description='Download and convert THP stories.')

    parser.add_argument('threads', metavar='THREADS', nargs='+', type=int, help='List of the threads of the story.')
    parser.add_argument('-u', '--url', metavar='URL', default='https://www.touhou-project.com/{}/res/{}.html', help='URL pattern from which the story will be downloaded, with the first {} as the forum, and the second as the thread.')
    parser.add_argument('-f', '--forum', metavar='FORUM', default='sdm', help='The name of the forum (example: sdm, th, etc.).')
    parser.add_argument('-o', '--only-op', action='store_true', help='Include only posts made by the original poster.')

    args = parser.parse_args()

    main(args.url, args.forum, args.only_op, args.threads)
