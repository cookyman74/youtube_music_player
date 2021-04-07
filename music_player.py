from tkinter import *
from tkinter import filedialog

import os
import sys

import mutagen
from mutagen.mp3 import MP3

import pygame
from pygame import mixer
from youtubePlayer import YtbListPlayer
import configparser

pygame.mixer.init()

# Title and dimensions
root = Tk()
root.geometry("600x280")
root.resizable(False, False)
root.title('Utb Audio Player')

# print(os.path.realpath(__file__))


# Main classes
class Audiobox(Frame):
    def __init__(self, master=None):
        super().__init__()

        # Frame settings
        api_key = 'AIzaSyDWcZTZfUp_xqT_QF7eftkiaMSFvu2UaBU'
        self.utbplayer = YtbListPlayer(api_key)
        self.master = master
        self.pack_propagate(0)
        self.config(width=260, height=160, bg="#FFF")
        self.grid(row=0, column=0, padx=10, pady=10)

        # Create Listbox
        def listbox_func(evnt):
            mixer.music.stop()
            self.songOffset = 0
            select_num = self.listbox.curselection()[0]
            if self.listbox.curselection():
                song = audiobox.song_list[select_num][1]
                if str(type(song)) == "<class 'pafy.backend_youtube_dl.YtdlStream'>":
                    # todo 유튜브 플레이 시간 & playtime bar
                    print("유튜브 플레이 시간정보")
                    input_pannel.timeBar.set(0)
                else:
                    audio = MP3(song)
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
        self.song_list = []  # Possess both the index and path of song (ex: song_list = [[0, "/song1.mp3"], [1, "song2.ogg"]])
        self.current_time = 0
        self.songOffset = 0

        self.isPlaying = False

    def add_song(self, files):
        if not files: return
        song_list = self.utbplayer.play_list
        for song in files:
            self.listbox.insert(len(self.song_list), os.path.splitext(os.path.basename(song))[0])
            song_list.append([len(self.song_list), os.path.realpath(song)])

    def add_youtubelist(self, url):
        self.utbplayer.set_playlist(url)
        self.utbplayer.set_playitems()
        music_lists = self.utbplayer.play_list

        for _, v in music_lists.items():
            title = v[0]
            play_url = v[1]
            self.listbox.insert(len(self.listbox.get(0)), title)
            self.song_list.append([len(self.song_list), play_url])

    def add_playlist(self, directory):
        if not directory: return
        files = os.listdir(directory)
        for song in files:
            noExtension = os.path.splitext(song)[0]
            self.song_list.append([len(self.song_list), os.path.realpath(directory) + '\\' + song])
            self.listbox.insert(len(self.listbox.get(0, END)), noExtension)

    def set_song(self, index):
        self.listbox.selection_clear(0, END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        self.current_time = 0

        song = audiobox.song_list[audiobox.listbox.curselection()[0]][1]
        audio = MP3(song)

        input_pannel.timeBar.config(to=int(audio.info.length))

    def play_youtube(self):
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return

        currentIndex = self.listbox.index(ACTIVE)
        print(self.song_list)
        print(self.listbox.get(0))
        if str(type(self.song_list[currentIndex][1])) == "<class 'pafy.backend_youtube_dl.YtdlStream'>":
            # 유튜브 플레이리스트
            if self.utbplayer.media_player is None:
                self.utbplayer.set_mediaplayer()

            player = self.utbplayer.media_player
            if str(player.get_state()) in ["State.Playing", "State.Opening"]:
                player.stop()
            else:
                player.play_item_at_index(currentIndex)
        else:
            # MP3파일 실행
            path = self.song_list[currentIndex][1]

            if mixer.music.get_busy() == False:
                mixer.music.load(path)
                self.set_song(currentIndex)
                mixer.music.play(loops=0, start=self.songOffset / 1000)
            else:
                self.songOffset += mixer.music.get_pos()
                mixer.music.stop()

    def play_song(self):
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return

        currentIndex = self.listbox.index(ACTIVE)
        path = self.song_list[currentIndex][1]

        if mixer.music.get_busy() == False:
            mixer.music.load(path)
            self.set_song(currentIndex)
            mixer.music.play(loops=0, start=self.songOffset / 1000)
        else:
            self.songOffset += mixer.music.get_pos()
            mixer.music.stop()

    def next_song(self):
        self.songOffset = 0
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return

        currentIndex = currentSelections[0] + 1
        if currentIndex > len(self.song_list) - 1: currentIndex = 0
        if mixer.music.get_busy() == True:
            mixer.music.stop()
            self.set_song(currentIndex)
            self.play_song()
        else:
            self.set_song(currentIndex)

    def back_song(self):
        self.songOffset = 0
        currentSelections = self.listbox.curselection()
        if len(currentSelections) == 0: return

        currentIndex = currentSelections[0] - 1
        if currentIndex < 0: currentIndex = 0
        if mixer.music.get_busy() == True:
            mixer.music.stop()
            self.set_song(currentIndex)
            self.play_song()
        else:
            self.set_song(currentIndex)


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
        self.volume.config(command=lambda f: mixer.music.set_volume(self.volume.get() / 100))
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
        self.next.pack(side=LEFT, fill=X, expand=1)

        # Linking button to functions
        self.pauseplay.config(command=audiobox.play_youtube)


audiobox = Audiobox(master=root)
input_pannel = InputPannel(master=root)

# Credits
Label(root, text="Made by cookyman ( cookyman@gmail.com )").grid(row=1, column=0)
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
        print("sldjflsjdflsjdflksdjflksjdlk")
        song = audiobox.song_list[audiobox.listbox.curselection()[0]][1]
        startTime = '00:00'
        if str(type(song)) == "<class 'pafy.backend_youtube_dl.YtdlStream'>":
            audiobox.utbplayer.set_mediaplayer()
            audio = audiobox.utbplayer.media_player
        else:
            audio = MP3(song)

        # Start Time
        if mixer.music.get_busy():
            print("hhhhhhhh")
            audiobox.current_time = (audiobox.songOffset + mixer.music.get_pos()) / 1000

            minutes = int(audiobox.current_time // 60)
            seconds = int(audiobox.current_time % 60)

            if minutes < 10: minutes = '0' + str(minutes)
            if seconds < 10: seconds = '0' + str(seconds)

            startTime = str(minutes) + ':' + str(seconds)
            input_pannel.timeBar.set(audiobox.current_time)

            if round(audio.info.length / audiobox.current_time, 2) <= 1:
                if input_pannel.autoplay.get() == 1:
                    audiobox.next_song()
                elif input_pannel.loop.get() == 1:
                    mixer.music.stop()
                    audiobox.songOffset = 0
                    audiobox.play_youtube()
                else:
                    mixer.music.stop()
                    audiobox.songOffset = 0
                    input_pannel.timeBar.set(0)
        else:
            print("333333")
            audiobox.current_time = audiobox.songOffset / 1000
            if audiobox.current_time > 0:
                minutes = int(audiobox.current_time // 60)
                seconds = int(audiobox.current_time % 60)

                if minutes < 10: minutes = '0' + str(minutes)
                if seconds < 10: seconds = '0' + str(seconds)

                startTime = str(minutes) + ':' + str(seconds)

        # End time
        minutes = int(audio.info.length // 60)
        seconds = int(audio.info.length % 60)

        if minutes < 10: minutes = '0' + str(minutes)
        if seconds < 10: seconds = '0' + str(seconds)

        minutes = str(minutes)
        seconds = str(seconds)

        input_pannel.timeLabel.config(text=startTime + ' | ' + minutes + ':' + seconds)

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
createTab("File", [["Add youtube Url(s)", lambda: audiobox.add_youtubelist(url)],
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