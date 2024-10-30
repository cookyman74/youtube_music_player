from tkinter import *
from tkinter import filedialog, simpledialog
from urllib import request
from PIL import ImageTk, Image
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import asyncio
import os
from player.ytb_list_player import YtbListPlayer  # YtbListPlayer는 재생 관리 모듈입니다
import configparser

class Audiobox(Frame):
    def __init__(self, master=None, audio=None):
        super().__init__(master)
        self.audio = audio
        self.master = master
        self.config(width=300, height=350, bg="#FFF")
        self.grid(row=0, column=0, padx=10, pady=10)

        # Create Listbox for Playlist
        def listbox_func(event):
            current_selections = self.listbox.curselection()
            if current_selections:
                index = current_selections[0]
                self.set_song(index)

        self.listbox = Listbox(self, selectmode='extended', width=40, height=20)
        self.listbox.bind('<<ListboxSelect>>', listbox_func)
        self.listbox.pack(side=LEFT)

        scrollbar = Scrollbar(self, width=20, orient=VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

    def add_song(self, files):
        for song in files:
            title = os.path.splitext(os.path.basename(song))[0]
            self.listbox.insert(END, title)
            self.audio.add_to_playlist(song)

    def add_youtubelist(self, url):
        self.audio.set_playlist(url)
        asyncio.run(self.audio.fetch_playlist_items())
        for audio in self.audio.add_list:
            title = re.sub(r"[^a-zA-Z0-9\'\"【​】\[\]#|가-힣()\-\.\,]", "_", audio.title)
            self.listbox.insert(END, title)
        self.audio.set_mediaplayer()

    def add_playlist(self, directory):
        files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(('.mp3', '.wav', '.ogg'))]
        self.add_song(files)

    def set_song(self, index):
        self.listbox.selection_clear(0, END)
        self.listbox.selection_set(index)
        self.listbox.activate(index)
        selected_song = self.audio.play_list[index]
        if isinstance(selected_song, str):
            # Local mp3 file
            audio_mp3 = MP3(selected_song)
            audio_tags = ID3(selected_song)
            length = int(audio_mp3.info.length)
            with open('selected_album_img.jpg', 'wb') as img:
                img.write(audio_tags.getall("APIC")[0].data)
        else:
            # YouTube audio
            audio_ytb = selected_song
            length = audio_ytb.length
            request.urlretrieve(audio_ytb.thumb, "selected_album_img.jpg")

        self.master.update_album_art("selected_album_img.jpg", length)

    def play_song(self):
        current_selection = self.listbox.curselection()
        if not current_selection:
            return
        index = current_selection[0]
        self.set_song(index)
        self.audio.play(index)

    def stop_song(self):
        self.audio.stop()

    def next_song(self):
        current_selection = self.listbox.curselection()
        if current_selection:
            index = (current_selection[0] + 1) % self.listbox.size()
            self.set_song(index)
            self.audio.play(index)

    def back_song(self):
        current_selection = self.listbox.curselection()
        if current_selection:
            index = (current_selection[0] - 1) % self.listbox.size()
            self.set_song(index)
            self.audio.play(index)

    def set_volume(self, volume):
        self.audio.set_volume(volume)

class InputPannel(Frame):
    def __init__(self, master=None, audiobox=None):
        super().__init__(master)
        self.audiobox = audiobox
        self.config(width=300, height=350, bg='#FFF')
        self.grid(row=0, column=1, padx=10, pady=10)

        # Album art and time display
        self.album_art = Label(self)
        self.album_art.grid(row=0, column=0, columnspan=4)

        # Time display
        self.time_label = Label(self, text="00:00 | 00:00", font=(None, 12))
        self.time_label.grid(row=1, column=0, columnspan=4)

        # Buttons
        self.back_button = Button(self, text="◄◄", command=self.audiobox.back_song)
        self.play_button = Button(self, text="►", command=self.audiobox.play_song)
        self.stop_button = Button(self, text="■", command=self.audiobox.stop_song)
        self.next_button = Button(self, text="►►", command=self.audiobox.next_song)

        self.back_button.grid(row=2, column=0)
        self.play_button.grid(row=2, column=1)
        self.stop_button.grid(row=2, column=2)
        self.next_button.grid(row=2, column=3)

        # Volume slider
        self.volume_slider = Scale(self, from_=0, to=100, orient=HORIZONTAL, command=lambda v: self.audiobox.set_volume(int(v)))
        self.volume_slider.set(100)
        self.volume_slider.grid(row=3, column=0, columnspan=4)

    def update_album_art(self, img_path, length):
        img = Image.open(img_path)
        img = img.resize((250, 250), Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        self.album_art.config(image=img)
        self.album_art.image = img
        self.time_label.config(text=f"00:00 | {length // 60:02}:{length % 60:02}")


if __name__ == "__main__":
    root = Tk()
    root.title("YouTube MP3 Player")
    root.geometry("650x400")

    config = configparser.ConfigParser()
    config.read('config.ini')
    api_key = config['DEFAULT'].get("API_KEY")

    ytb_player = YtbListPlayer(api_key=api_key)
    audiobox = Audiobox(master=root, audio=ytb_player)
    input_pannel = InputPannel(master=root, audiobox=audiobox)

    menu_bar = Menu(root)
    root.config(menu=menu_bar)

    def add_youtube_playlist():
        url = simpledialog.askstring("URL", "Enter YouTube Playlist URL:")
        if url:
            audiobox.add_youtubelist(url)

    def add_local_files():
        files = filedialog.askopenfilenames(filetypes=[('Music Files', '*.mp3 *.wav *.ogg')])
        if files:
            audiobox.add_song(files)

    def add_playlist_directory():
        directory = filedialog.askdirectory()
        if directory:
            audiobox.add_playlist(directory)

    file_menu = Menu(menu_bar, tearoff=0)
    file_menu.add_command(label="Add YouTube URL(s)", command=add_youtube_playlist)
    file_menu.add_command(label="Add Files", command=add_local_files)
    file_menu.add_command(label="Add Playlist Directory", command=add_playlist_directory)
    menu_bar.add_cascade(label="File", menu=file_menu)

    root.mainloop()
