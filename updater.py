import os
from tkinter import Tk, Entry, Text, IntVar, Checkbutton, Button, END, Menu, Listbox, LEFT, RIGHT, BOTTOM, Toplevel
from tkinter.messagebox import showerror
import zipfile
import urllib
import shutil
import time
import webbrowser
try:
    from git import Repo
except:
    temp = open('errlog.txt', 'a')
    temp.write('Git not present\n')
    temp.close()
    raise ImportError
#from pyinstaller.__main__ import run as pyinstaller
def cleanup():
    if os.path.exists(os.getcwd()+'\\python37.zip'):
        os.remove('python37.zip')
    if os.path.exists(os.getcwd()+'\\get-pip.py'):
        os.remove('get-pip.py')
    if os.path.exists(os.getcwd()+'\\python'):
        shutil.rmtree('python')
def main():
    cleanup()
    #open new tkinter window
    #use pyinstaller('thp2epub.py', 'onefile') (? Correct?) to package thp2epub
    #use pyinstaller to package updater.py
    #finish
    updatewindow = Tk()
    updatewindow.title('Checking for Updates')
    #consolelog = Text(updatewindow)
    #consolelog.pack()
    urllib.request.urlretrieve('https://www.python.org/ftp/python/3.7.3/python-3.7.3-embed-amd64.zip', 'python37.zip')
    zip_ref = zipfile.ZipFile('python37.zip', 'r')
    zip_ref.extractall('python')
    zip_ref.close()
    urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', 'get-pip.py')
    os.system(os.getcwd()+'\\python\\python.exe get-pip.py')
    os.system('pip install pyinstaller')#os.getcwd()+'\\python\\python.exe -m
    try:
        repo = Repo.clone_from('https://github.com/Anonark/THP2Epub', os.path.join(os.getcwd(), 'git'+str(int(time.time()))))
        lastcommit = repo.head.commit
    except ImportError:
        showerror(title='Git not found', message='Git is not installed! Get it here: https://git-scm.com/downloads')
        updatewindow.destroy()
        webbrowser.open('https://git-scm.com/downloads')
        cleanup()
        temp = open('errlog.txt', 'a')
        temp.write('Git not present\n')
        temp.close()
        return
    except:
        #could not clone from repo, end
        showerror(title='Failed to clone from repo!', message='Could not clone files from https://github.com/Anonark/THP2Epub')
        updatewindow.destroy()
        cleanup()
        return
    if lastcommit.committed_date > int(os.path.getmtime('thp2epub.exe')):  
        try:
            os.system('pyinstaller '+os.getcwd()+'\\git\\thp2epub.py -F')
            #pyinstaller.run([os.path.join('git', 'thp2epub.py'), '-F'])
        except:
            showerror(title='Failed to package thp2epub.py', message='Update failed due to packaging error!')
            updatewindow.destroy()
            cleanup()
            temp = open('errlog.txt', 'a')
            temp.write('Packaging failed\n')
            temp.close()
            return
        
        #move thp2epub.exe from dist/ to main folder, then delete dist/ and git/
        
        temp = open('delreplace.bat', 'w')
        temp.write('taskkill /f /im thp2epub.exe\ndel thp2epub.exe\nmove \\dist\\thp2epub.exe \\\nrmdir /s /q \\python\nrmdir /s /q \\dist\ndel python37.zip\ncopy /b thp2epub.exe+\nstart thp2epub.exe\n( del /q /f "%~f0" >nul 2>&1 & exit /b 0  )')
        temp.close()
        os.startfile('delreplace.bat')
    else:
        showerror(title='No updates required!', message='Your THP2Epub is up to date!')
        updatewindow.destroy()
        cleanup()
        return
    updatewindow.mainloop()