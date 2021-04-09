import os
from tkinter.filedialog import askdirectory
from tkinter import *
import tkinter.messagebox
from pygame import mixer
from mutagen.id3 import ID3
from tkinter import ttk
from ttkthemes import themed_tk as tk

#creating a root window

root = tk.ThemedTk()       # Creates an object for the ThemedTk wrapper for the normal Tk class
root.get_themes()           # Returns a list of all themes that can be set
root.set_theme("aquativo")
root.title("PlayNow")
root.iconbitmap(r'title.ico')

#creating lists to store songs from playlist
lists = []
real = []

#topframe stores label and listbox while middleframe stores play,pause buttons
topframe= Frame(root)
topframe.pack()

middleframe= Frame(root)
middleframe.pack(pady=15,padx=15)

index = 0
songname = 0

text = ttk.Label(topframe, text='feel the beat')
text.pack(pady=10)

v = StringVar()
songlabel = Label(root, textvariable=v, width=35)
songlabel.pack()

#creating a listbox inside the topframe
listbox = Listbox(topframe)
listbox.pack()

#defining functions
def directorys():
    directory = askdirectory()
    os.chdir(directory)

    for files in os.listdir(directory):
        if files.endswith(".mp3"):

            realdir = os.path.realpath(files)
            audio = ID3(realdir)
            real.append(audio['TIT2'].text[0])

            lists.append(files)
    real.reverse()

    for items in real:
        listbox.insert(0, items)

    real.reverse()

# initializing_the_mixer
mixer.init()

def play():
   try:
       paused           #paused is initialised
   except:
         try:
             mixer.music.load(lists[index])
             mixer.music.play()
             statusbar['text']='Playing '+''+os.path.basename(lists[index])
         except:
             tkinter.messagebox.showerror('File not found', 'Add a song to play')
   else:
        mixer.music.unpause()
        statusbar['text'] = 'Playing '+''+os.path.basename(lists[index])

def update():
    global index
    global songname
    v.set(real[index])

def stop():
    try:
        global paused
        paused= TRUE
        mixer.music.pause()
        statusbar['text'] = 'Playing paused'
        v.set("")
    except:
        tkinter.messagebox.showerror('File not found', 'Add a song to play')

def next():
    try:
        global index
        index +=1
        mixer.music.load(lists[index])
        mixer.music.play()
        statusbar['text']= 'Playing '+''+os.path.basename(lists[index])
        update()
    except:
        tkinter.messagebox.showerror('File not found', 'Add a song to play')

def prv():
    try:
        global index
        index -= 1
        mixer.music.load(lists[index])
        mixer.music.play()
        update()
        statusbar['text'] = 'Playing ' + '' + os.path.basename(lists[index])
    except:
        tkinter.messagebox.showerror('File not found', 'Add a song to play')

def setvol(val):
    volume = int(val)/100    #typecasting(string into int)
    mixer.music.set_volume(volume)

def about():
    tkinter.messagebox.showinfo('version 1.0','Developed by developers from Bangalore,India')



#adding buttons to GUI
playphoto = PhotoImage(file='play.png')
playbtn = ttk.Button(middleframe, image=playphoto,command=play)
playbtn.grid(row=0,column=1,padx=3)

stopphoto = PhotoImage(file='pause.png')
stopbtn = ttk.Button(middleframe, image=stopphoto, command=stop)
stopbtn.grid(row=0,column=2,padx=3)

nextphoto = PhotoImage(file='next.png')
nextbtn = ttk.Button(middleframe, image=nextphoto, command=next)
nextbtn.grid(row=0,column=3,padx=3)

prvphoto = PhotoImage(file='back.png')
prvbtn = ttk.Button(middleframe, image=prvphoto, command=prv)
prvbtn.grid(row=0,column=0,padx=3)

addbtn= ttk.Button(topframe,text='+ADD',command= directorys)
addbtn.pack()

#volume control

scale = Scale(root, from_=0, to=100, orient=HORIZONTAL, command=setvol)
scale.set(55)
mixer.music.set_volume(55)
scale.pack(pady=10)

#creating a menubar
menubar= Menu(root)
root.config(menu=menubar)

submenu =Menu (menubar, tearoff=0)
menubar.add_cascade(label='File', menu=submenu)
submenu.add_command(label='Browse', command= directorys)
submenu.add_command(label='Exit',command=root.destroy)

submenu =Menu (menubar, tearoff=0)
menubar.add_cascade(label='Help',menu=submenu)
submenu.add_command(label='About us',command= about)

statusbar=Label(root,text="Playnow",relief=SUNKEN, anchor=W)
statusbar.pack(side=BOTTOM, fill=X,anchor=W)







root.mainloop()
