from tkinter import *
from tkinter import filedialog
from tkinter import simpledialog


import os
import sys

import mutagen
from mutagen.mp3 import MP3

import pygame
from pygame import mixer
from youtubePlayer import YtbListPlayer

pygame.mixer.init()

# Title and dimensions
root = Tk()
root.geometry("600x280")
root.resizable(False, False)
root.title('Utb Audio Player')

# print(os.path.realpath(__file__))


# Main classes
class Audiobox(Frame):
    def __init__(self, master=None, audio=None):
        super().__init__()

        # Frame settings
        self.audio = audio
        self.master = master
        self.pack_propagate(0)
        self.config(width=260, height=160, bg="#FFF")
        self.grid(row=0, column=0, padx=10, pady=10)

        # Create Listbox
        def listbox_func(evnt):
            try:
                self.audio.media_player.stop()
            except:
                pass
            self.songOffset = 0
            select_num = self.listbox.curselection()[0]
            song_list = self.audio.play_list  #플레이리스트 받아오기
            if self.listbox.curselection():
                song = song_list[select_num]
                if str(type(song)) == "<class 'pafy.backend_youtube_dl.YtdlPafy'>" and song:
                    # 유튭플레이용 pafy객체인지에 따라 타이머바 초깃값 설정.
                    input_pannel.timeBar.config(to=int(song.length))
                    input_pannel.timeBar.set(0)
                else:
                    audio = MP3(song)
                    print("mp3길이: ", int(audio.info.length))
                    input_pannel.timeBar.config(to=int(audio.info.length))
                    input_pannel.timeBar.set(0)

        self.listbox = Listbox(self, selectmode='extended', width=40)
        self.listbox.bind('<<ListboxSelect>>', listbox_func)
        self.listbox.pack(side=LEFT)

        # Add and configure scrollbar
        scrollbar = Scrollbar(self, width=20, orient=VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.listbox.config(yscrollcommand=scrollbar.set)

        # Song tracking variable
        self.current_song = None  # Possess the index of the current song
        self.current_time = 0
        self.songOffset = 0
        self.isPlaying = False

    def add_song(self, files):
        if not files: return

        for song in files:
            self.listbox.insert(len(self.audio.play_list), os.path.splitext(os.path.basename(song))[0])
            self.audio.play_list.append(os.path.realpath(song))

    def add_youtubelist(self, url):
        self.audio.set_playlist(url)
        self.audio.set_utbplay_items()

        for audio in self.audio.play_list:
            title = audio.title
            self.listbox.insert(len(self.audio.play_list), title)

    def add_playlist(self, directory):
        if not directory: return
        files = os.listdir(directory)
        song_list = self.utbplayer.play_list
        index = max(song_list.keys()) + 1
        for song in files:
            noExtension = os.path.splitext(song)[0]
            song_list[index] = os.path.realpath(directory) + '\\' + song
            self.listbox.insert(len(self.listbox.get(0, END)), noExtension)
            index += 1

    def set_song(self, index):
        self.listbox.selection_clear(0, END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.current_time = 0

        # song = self.audio.media_player[audiobox.listbox.curselection()[0]]
        # input_pannel.timeBar.config(to=int(song.length))

    def play_song(self):
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return

        self.audio.set_mediaplayer()

        player = self.audio.media_player
        currentIndex = self.listbox.index(ACTIVE)
        player.play_item_at_index(currentIndex)

        # 유튜브 플레이리스트
        # if self.audio.media_player is None:
        #     self.audio.set_utbplay_items()

    def stop_song(self):
        player = self.audio.media_player
        player.stop()

    def next_song(self):
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return
        self.audio.media_player.next()
        currentIndex = int(currentSelections[0]) + 1
        self.set_song(currentIndex)

    def back_song(self):
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return

        currentIndex = currentSelections[0] - 1
        if currentIndex < 0: currentIndex = 0
        self.audio.media_player.previous()
        self.set_song(currentIndex)

    def set_volume(self, volume):
        # https://stackoverflow.com/questions/45150694/how-to-change-the-volume-of-playback-in-medialistplayer-with-libvlc
        player = self.audio.media_player
        player.get_media_player().audio_set_volume(volume)


class InputPannel(Frame):
    def __init__(self, master=None):
        super().__init__()

        # Pannel configuration
        self.config(width=250, height=160, bg='#FFF')  # , bg="#bdbdbd"
        self.grid(row=0, column=1, padx=0)

        # self.grid_propagate(0)

        # Adding details
        def setVolumeBar(event):
            self.volume.event_generate("<Button-3>", x=event.x, y=event.y)
            return

        self.volume = Scale(root, length=150, from_=100, to=0);
        self.volume.set(100)
        self.volume.config(command=lambda f: audiobox.set_volume(int(self.volume.get())))
        self.volume.bind('<Button-1>', setVolumeBar)
        self.timeLabel = Label(self, text="00:00 | 00:00", font=(None, 12, "italic"))  # Time indicator
        self.timeLabel.config(bd=5, relief=GROOVE)  # width=22,

        def func(ev):
            if mixer.music.get_busy() == False:
                audiobox.songOffset = self.timeBar.get() * 1000

        def setTimeBar(event):
            mixer.music.stop()
            self.timeBar.event_generate("<Button-3>", x=event.x, y=event.y)
            return

        self.timeBar = Scale(self, orient=HORIZONTAL, showvalue=False)  # Time bar
        self.timeBar.config(length=250, command=func)
        self.timeBar.bind('<Button-1>', setTimeBar)
        self.timeBar.bind('<Button-3>', lambda f: mixer.music.stop())

        # Loop and Autoplay variables
        self.autoplay = IntVar()
        self.autoplay.set(False)

        self.loop = IntVar()
        self.loop.set(False)

        autoplay = Checkbutton(self, text="Autoplay", font=(None, 11), anchor='w', var=self.autoplay,
                               command=lambda: self.loop.set(False))
        loop = Checkbutton(self, text="Loop", font=(None, 11), anchor='w', var=self.loop,
                           command=lambda: self.autoplay.set(False))

        # Making the control buttons
        bFrame = Frame(self, bg='#FFF')
        self.back = Button(bFrame, text="Prev", font=(None, 11))  # Back button
        self.pauseplay = Button(bFrame, text="Pause / Play", font=(None, 11))  # Play and Pause button
        self.stop = Button(bFrame, text="stop", font=(None, 11))  # Play and Pause button
        self.next = Button(bFrame, text="Next", font=(None, 11))  # Next button

        self.next.config(command=audiobox.next_song)  # Next song binding
        self.back.config(command=audiobox.back_song)  # Back song binding

        # Placing the items
        self.timeLabel.grid(row=0, column=0, sticky='nsew')
        self.volume.grid(row=0, column=3)

        self.timeBar.grid(row=1, column=0)
        autoplay.grid(row=2, column=0, sticky='nsew')
        loop.grid(row=3, column=0, sticky='nsew')

        bFrame.grid(row=4, column=0, sticky='nsew')

        self.back.pack(side=LEFT, fill=X, expand=1)
        self.pauseplay.pack(side=LEFT, fill=X, expand=1)
        self.stop.pack(side=LEFT, fill=X, expand=1)
        self.next.pack(side=LEFT, fill=X, expand=1)

        # Linking button to functions
        self.pauseplay.config(command=audiobox.play_song)
        self.stop.config(command=audiobox.stop_song)



api_key = 'AIzaSyDWcZTZfUp_xqT_QF7eftkiaMSFvu2UaBU'
utbplayer = YtbListPlayer(api_key)

audiobox = Audiobox(master=root, audio=utbplayer)
input_pannel = InputPannel(master=root)

# Credits
Label(root, text="Made by cookyman").grid(row=1, column=0)
Label(root, text="https://scv-life.tistory.com/", fg="blue").grid(row=2, column=0)

# Menu bar and it's tabs
menuBar = Menu(root)
root.config(menu=menuBar)


def createTab(name, added_commands, parent):
    tab = Menu(parent, tearoff=0)
    for command in added_commands:
        tab.add_command(label=command[0], command=command[1])

    parent.add_cascade(label=name, menu=tab)


# Timer update
def update():
    if audiobox.listbox.curselection():
        player = audiobox.audio.media_player
        try:
            play_state = player.get_state()
            total_length = player.get_media_player().get_length() / 1000
            total_minutes = int(total_length // 60)
            total_seconds = int(total_length % 60)
            totalTime = "{0:02d} : {1:02d}".format(total_minutes, total_seconds)
        except Exception as err:
            play_state = False

        if str(play_state) in ["State.Opening", "State.Playing"]:
            running_length = player.get_media_player().get_time() / 1000
            running_minutes = int(running_length // 60)
            running_seconds = int(running_length % 60)
            startTime = "{0:02d} : {1:02d}".format(running_minutes, running_seconds)
            # todo : 트래킹 바 구현
            # input_pannel.timeBar.set(audiobox.current_time)
        else:
            print("*"*100)
            total_minutes = 0
            total_seconds = 0
            running_minutes = 0
            running_seconds = 0
            totalTime = "{0:02d} : {1:02d}".format(total_minutes, total_seconds)
            startTime = "{0:02d} : {1:02d}".format(running_minutes, running_seconds)
        input_pannel.timeLabel.config(text=startTime + ' | ' + totalTime)
    root.after(250, update)


def clear_audiobox():
    mixer.music.stop()
    audiobox.listbox.delete(0, END)
    audiobox.song_list = []
    input_pannel.timeLabel.config(text='00:00 | 00:00')


def remove_tracks():
    if len(audiobox.song_list) == 0: return
    new_list = []
    index = 0
    for item in audiobox.song_list:
        if item[0] not in audiobox.listbox.curselection():
            new_list.append([index, item[1]])
            index += 1
    audiobox.song_list = new_list
    mixer.music.stop()

    for i in audiobox.listbox.curselection()[::-1]:
        audiobox.listbox.delete(i)
    input_pannel.timeLabel.config(text='00:00 | 00:00')


url = 'https://www.youtube.com/playlist?list=PL7283475-4cpXpbZJdgNWOVh0nvMbDCH7'
createTab("File", [["Add youtube Url(s)", lambda: audiobox.add_youtubelist(
simpledialog.askstring("url", "유튭플레이리스트URL")
)],
                   ["Add Files(s)", lambda: audiobox.add_song(
                       filedialog.askopenfilenames(filetypes=[('Music files', '.wav .mp3 .ogg')]))],
                   ["Add Playlist dir", lambda: audiobox.add_playlist(filedialog.askdirectory())]], menuBar)
createTab("Edit", [['Remove Track(s)', remove_tracks], ["Clear Audiobosx", clear_audiobox]], menuBar)


def destroy_func(event):
    mixer.music.stop()

root.bind('<Destroy>', destroy_func)
root.after(100, update)
root.mainloop()
pygame.quit()