import os
from tkinter.messagebox import showerror

def genlibs(libmeta):
    global libdict
    listfiles = os.listdir(os.path.join(os.getcwd(), 'epubs'))
    libchk = open(libmeta, 'r')
    temp = [line.split(':') for line in libchk.readlines()]
    libdict = {}
    for i in temp:
        libdict[i[0]] = i[1:]
    liblist = []
    for file in listfiles:
        if file in libdict:
            liblist.append(libdict[file])
    return liblist

def openepub(name):
    global libdict
    for path, tags in libdict.items():
        if tags == name:
            try:
                os.startfile(os.path.join('epubs', path))
            except:
                showerror(title='File does not exist', message='The epub you are trying to open does not exist!')
