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

from lxml import etree, html
from lxml.builder import E
from time import strptime, strftime
from datetime import datetime
import time
from threading import Thread as multithread
#from argparse import ArgumentParser

import updater

from functions import generate

import parselibrary

import os
import sys

from tkinter import Tk, Entry, Text, IntVar, Checkbutton, Button, END, Menu, Listbox, LEFT, RIGHT, BOTTOM, Toplevel
from tkinter.messagebox import showerror

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
    def __init__(self, op, replies, title):
        self.op = op
        self.replies = replies
        self.title = title
        if self.title is None:
            self.title = 'blank'
        self.author = op.author
        
    def postlen(self, post):
        length = 0
        for i in post.content:
            length += len(etree.tostring(i))
        return length

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
        sortmean = [i for i in self.replies if self.postlen(i) > 0]
        #sortmean.sort(key=lambda x: self.postlen(x))
        mean = sum(self.postlen(i) for i in sortmean) / len(sortmean)
        #print('mean reply length:', mean)

        if self.author.name == 'Anonymous' or self.author.name == '' or self.author.name == None:
            only_op = False
        for reply in self.replies:
            # Remove user answers if not wanted.
            if only_op and not reply.is_op(self.op):
                continue
            if not only_op and self.postlen(reply) < mean:
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
        if self.author.render() == op.author.render() or (self.author.trip == op.author.trip and self.author.trip != ''):
            return True
        return False
        """if self.author.trip is not None:
            return self.author.trip == op.author.trip
        elif self.author.name is not None:
            return self.author.name == op.author.name"""

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
    def __init__(self, name, url):
        self.name = name
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
        if self.name is not None and self.trip is not None:
            return '{}{}'.format(self.name, self.trip)
        elif self.name is not None:
            return self.name
        else:
            return 'Anonymous'
        
class SearchResult(object):
    def __init__(self, title, author, forum, links):
        self.title = title
        self.author = author
        if self.author is None:
            self.author = 'Anonymous'
        self.forum = forum
        self.links = links
        
    def __repr__(self):
        return self.title + ' by ' + self.author + ' in ' + self.forum + '\n'

def searchstory(title, results):
    global finaldict
    finaldict = {}
    results.delete(0, END)
    if not os.path.exists('storylistcache.txt') or (os.path.exists('storylistcache.txt') and (len(open('storylistcache.txt', 'r', encoding='utf-8').read()) == 0 or int(time.time()) - os.path.getmtime('storylistcache.txt') > 1209600)):
        recache()
    tree = html.document_fromstring(open('storylistcache.txt', 'r', encoding='utf-8').read()).getroottree()
    root = tree.find('//body').find('div[@id="list"]')
    #print('root', root)
    listofcyoa = root.xpath("//td[@class='listentry cyoa']")
    #print('listofcyoa:', listofcyoa)
    cyoatuples = []
    for cyoa in listofcyoa:
        storytitle = cyoa.find('b').find("span[@style='color:purple']").text
        storyauthor = cyoa.find("span[@style='color:maroon']").find('b').text
        storyforum = cyoa.find('b').find('a').find("span[@style='color:blue']").text
        #print('cyoa:', storytitle, storyauthor)
        storylinks = cyoa.xpath('a[starts-with(@href, "http://www.touhou-project.com")]')
        try:
            storythreads = [int(i.text) for i in storylinks]
        except:
            continue
        cyoatuples.append(SearchResult(storytitle, storyauthor, storyforum, storythreads))
    searchresults = []
    for double in cyoatuples:
        if title.lower() in double.title.lower() or (double.author is not None and title.lower() in double.author.lower()):
            searchresults.append(double)
    #print('searchresults:', searchresults)
    searchresults.sort(key=lambda x:x.title.lower())
    for result in searchresults:
        finaldict[result.__repr__()] = result
        results.insert(END, result)
        
def setthreadandforum(searchresult, threadentry, forumentry):
    threadentry.delete(0, END)
    forumentry.delete(0, END)
    temp = ""
    for i in searchresult.links:
        temp += str(i) + " "
    threadentry.insert(END, temp[:-1])
    forumentry.insert(END, searchresult.forum)

def gettag(tree, tag, tclass=None):
    # dfs to find 'label', 'blockquote', etc.
    if tree.tag == tag:
        if tclass is None:
            return tree
        else:
            if tree.get('class') == tclass:
                return tree
    for temp in tree:
        found = gettag(temp, tag, tclass)
        if found is not None: #and ((tclass is None and found.tag == tag) or (tclass is not None and found.attrib['class'] == tclass)):
            return found
    return None


def parse_post(root, consolelog, downloadimg):
    # We use the filesize element because it contains the image name.
    label = gettag(root, 'label')
    if downloadimg:
        fileprops = gettag(root, 'span', 'fileprops')
        if fileprops is not None:
            thumblink = gettag(fileprops, 'a', 'thumblink')
            try:
                name = gettag(fileprops, 'span', 'forigname').text
                url = thumblink.get('href')
                '''a = filesize.getnext().getnext()
                filesize = etree.tostring(filesize, method='text', encoding='UTF-8')
                filesize = filesize.split()
                name = filesize[7:-2]'''
                '''name = b' '.join(name)
                try:
                    name = name.decode('UTF-8')
                except UnicodeDecodeError:
                    for i in range(-5, -42, -1):
                        char = name[i] if type(name[i]) is int else ord(name[i])
                        if char & 0xc0 == 0xc0:
                            name = name[:i-1] + b'\xef\xbf\xbd' + name[-4:]
                            break
                    name = name.decode('UTF-8')'''
                #filesize, size = filesize[3][1:], filesize[5]
                '''if a.tag == 'a':
                    url = a.get('href')
                    a.attrib['href'] = name
                else:
                    url = a.find('img').get('src')
                    a.find('img').attrib['src'] = name'''
                name = name + url[-4:]
                image = Image(name, url) #replace with none if image packing doesnt work
                if len(name) > 0:
                    consolelog.insert(END, 'Added image '+ name+ ' to post\n')
                    consolelog.see(END)
            except AttributeError:
                image = None
        else:
            image = None
        thumbsrc = gettag(root, 'img', 'thumb')
        if thumbsrc is not None:
            thumbsrc.attrib['src'] = image.name
    else:
        image = None

    #label = root.find('label')
    
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
    #title = label.find('span[@class="filetitle"]')
    title = gettag(label, 'span', 'filetitle')
    title = title.text.strip() if title is not None else None
    name = gettag(label, 'span', 'postername')
    if name is not None:
        a = name.find('a')
        if a is not None:
            #mail = a.get('href')
            name = a.text
        else:
            #mail = ''
            name = name.text

    #postertrip = label.find('span[@class="postertrip"]')
    postertrip = gettag(label, 'span', 'postertrip')
    if postertrip is not None:
        trip = postertrip.text
    else:
        trip = ''
    if name == '':
        name = None
    author = Author(name, trip, None)
    last = gettag(label, 'span', 'posttime')
    try:
        if last is not None:
            date = strptime(last.text.strip(), '%y/%m/%d(%a)%H:%M')
        else:
            date = strptime(label[-1].tail.strip(), '%y/%m/%d(%a)%H:%M')
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
    if blockquote.text is not None:
        temp = etree.Element('br')
        temp.text = blockquote.text.strip()#.encode('utf-8')
        content.append(temp)
    for item in blockquote:
        if item is str and item.strip() == '':
            continue
        content.append(item)

    return Post(title, author, date, image, content)


def parse_thread(url, consoletext, downloadimg):
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
        op = parse_post(root, consoletext, downloadimg)
    
        replies = []
        td = root.findall('.//td[@class="reply"]')
        for reply in td:
            replies.append(parse_post(reply, consoletext, downloadimg))
            
            
        consoletext.insert(END, 'Finished parsing thread!\n')
        consoletext.see(END)
        title = gettag(root, 'span', 'filetitle')
        return Thread(op, replies, title.text.strip() if title is not None else None)
    except HTTPError:
        consoletext.insert(END, 'Thread not found!\n')
        consoletext.see(END)
        return

def main(url, forum, only_op, threads, consoletext, downloadimg):
    global curstory
    consoletext.delete(1.0,END)
    try:
        threads = [int(i) for i in threads]
    except:
        consoletext.insert(END, 'Invalid characters found in thread list!')
        consoletext.see(END)
        return
    threads_list = []
    for thread in threads:
        consoletext.insert(END, 'Rendering of thread №{}…\n'.format(thread))
        consoletext.see(END)
        t = parse_thread(url.format(forum, thread), consoletext, downloadimg)
        threads_list.append(t)

        html = t.render(only_op)

        # Use b mode as it allows us to directly dump UTF-8 data.
        consoletext.insert(END, 'Downloaded thread №{}, generating XHTML...\n'.format(thread))
        consoletext.see(END)
        with open('{}.xhtml'.format(thread), 'wb') as f:
            f.write(etree.tostring(html, pretty_print=True, xml_declaration=True, doctype='<!DOCTYPE html SYSTEM "/tmp/test.dtd">', encoding='UTF-8'))

    consoletext.insert(END, 'Finished downloading threads! Now generating Epub...\n')
    consoletext.see(END)

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
    invalidchars = [':', '<', '>', '"', '/', '\\', '|', '?', '*']
    if curstory is None:
        curstory = SearchResult(t.title, t.author.render(), forum, threads)
    temptitle = curstory.title
    tempauthor = curstory.author
    tempforum = curstory.forum
    if tempauthor is None:
        tempauthor = 'Anonymous'
    if tempforum is None:
        tempforum = 'unknown'
    for i in invalidchars:
        temptitle = temptitle.replace(i, '')
    try:
        os.mkdir('epubs')
    except:
        pass
    makeepub = multithread(target=generate, args=(list_chaps, temptitle, tempauthor, "1", str(len(list_chaps)), threads_list))
    makeepub.start()
    makeepub.join()
    tempttl = temptitle + "_" + "1" + "-" + str(len(list_chaps)) + ".epub"
    if os.path.exists(os.path.join('epubs', tempttl)):
        os.remove(os.path.join('epubs', tempttl))
    os.rename(tempttl, os.path.join('epubs', tempttl))
    if not os.path.exists(os.path.join('epubs', 'libmeta.txt')):
        open(os.path.join('epubs', 'libmeta.txt'), 'w')
    with open(os.path.join('epubs', 'libmeta.txt'), 'r+') as libmeta:
        for line in libmeta.readlines():
            if temptitle + "_" + "1" + "-" + str(len(list_chaps)) + ".epub" in line:
                break
        else:
            libmeta.write(temptitle + "_" + "1" + "-" + str(len(list_chaps)) + ".epub"+':'+temptitle+':'+tempauthor+':'+tempforum+'\n')
    consoletext.insert(END, 'Finished all operations! The story has been saved as ' + temptitle + "_" + "1" + "-" + str(len(list_chaps)) + ".epub")
    consoletext.see(END)

def recache(consoletext=None):
    cache = open('storylistcache.txt', 'w', encoding='utf-8')
    cache.write(urlopen("https://www.touhou-project.com/storylist.php").read().decode('utf-8'))
    cache.close()
    if consoletext is not None:
        consoletext.delete(0, END)
        consoletext.insert(END, 'Recached Successfully!')
        consoletext.see(END)

def restart():
    os.execl(sys.executable, sys.executable, * sys.argv)
    
def searchresultandsavetitle(searchresults, story, forum):
    global finaldict, curstory
    
    curstory = finaldict[searchresults.get(searchresults.curselection())]
    setthreadandforum(finaldict[searchresults.get(searchresults.curselection())], story, forum)
    
def openlib(window):
    if os.path.exists(os.path.join(os.getcwd(), 'epubs')):
        listlibs = parselibrary.genlibs(os.path.join('epubs', 'libmeta.txt'))
        librarywindow = Toplevel(window)
        librarywindow.title('Thread Library')
        #list of downloaded books
        listbooks = Listbox(librarywindow, width=60)
        parsedlibs = []
        for lib in listlibs:
            parsedlibs.append(lib[0] + ' by ' + lib[1] + ' in ' + lib[2])
        for lib in parsedlibs:
            listbooks.insert(END, lib)
        listbooks.bind("<Double-Button-1>", lambda _:parselibrary.openepub(listlibs[listbooks.curselection()[0]]))
        listbooks.pack()
        librarywindow.mainloop()
    else:
        showerror(title='No downloaded files!', message='You need to have downloaded some files to be able see your library!')
    

if __name__ == '__main__':
    curstory = None
    # do GUI
    mainwindow = Tk()
    mainwindow.title('THP2Epub')
    #write widgets
    #restart button
    filemenu = Menu(mainwindow)
    filemenu.add_command(label="Restart Program", command=restart)
    
    #recache button
    filemenu.add_command(label="Recache Storylist", command=lambda:recache(consolelog))
    
    #view downloaded library
    filemenu.add_command(label="View Downloaded", command=lambda:openlib(mainwindow))
    
    #check for updates
    filemenu.add_command(label="Update", command=updater.main)
    
    mainwindow.config(menu=filemenu)
    
    #show console log
    consolelog = Text(mainwindow)
    consolelog.pack()
    #get forum name
    forum = Entry(mainwindow, width=60)
    forum.insert(END, 'Forum Name (EX: sdm)')
    forum.pack(side=BOTTOM)
    
    #get thread ids (title search coming soon)
    story = Entry(mainwindow, width=60)
    story.insert(END, 'Thread IDs (EX: 142 255 2736)')
    story.pack(side=BOTTOM)
    
    #searchbar
    searchbar = Entry(mainwindow, width=60)
    searchbar.insert(END, 'Search title or author')
    searchbar.pack()
    
    #search button
    searchbutton = Button(mainwindow, text='Search', command=lambda:searchstory(searchbar.get(), searchresults))
    searchbutton.pack()
    
    #search results
    searchresults = Listbox(mainwindow, width=150)
    searchresults.bind("<Double-Button-1>", lambda _:searchresultandsavetitle(searchresults, story, forum))
    searchresults.pack(side=LEFT)
    
    #only get op posts?
    onlyop = IntVar(value=1)
    Checkbutton(mainwindow, text="Download only OP posts?", variable=onlyop).pack(side=BOTTOM)
    
    #download images?
    downloadimg = IntVar(value=0)
    Checkbutton(mainwindow, text="Download images?", variable=downloadimg).pack(side=BOTTOM)
    
    #download button
    downloadbutton = Button(mainwindow, text='Download', command=lambda: multithread(target=main, args=('https://www.touhou-project.com/{}/res/{}.html', forum.get(), True if onlyop.get() == 1 else False, story.get().split(), consolelog, True if downloadimg.get() == 1 else False)).start())
    downloadbutton.pack(side=BOTTOM)
    
    mainwindow.mainloop()
    """parser = ArgumentParser(description='Download and convert THP stories.')

    parser.add_argument('threads', metavar='THREADS', nargs='+', type=int, help='List of the threads of the story.')
    parser.add_argument('-u', '--url', metavar='URL', default='https://www.touhou-project.com/{}/res/{}.html', help='URL pattern from which the story will be downloaded, with the first {} as the forum, and the second as the thread.')
    parser.add_argument('-f', '--forum', metavar='FORUM', default='sdm', help='The name of the forum (example: sdm, th, etc.).')
    parser.add_argument('-o', '--only-op', action='store_true', help='Include only posts made by the original poster.')

    args = parser.parse_args()

    main(args.url, args.forum, args.only_op, args.threads)"""
