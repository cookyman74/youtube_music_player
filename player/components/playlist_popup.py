# 플레이리스트 등록 팝업

# player/components/playlist_popup.py
import tkinter as tk
from tkinter import simpledialog


class PlaylistPopup(tk.Toplevel):
    def __init__(self, master, player):
        super().__init__(master)
        self.title("Register Playlist")
        self.geometry("300x150")
        self.player = player
        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self, text="Enter YouTube Playlist URL")
        label.pack(pady=5)

        self.url_entry = tk.Entry(self, width=40)
        self.url_entry.pack(pady=10)

        add_button = tk.Button(self, text="Add", command=self.add_playlist)
        add_button.pack(pady=10)

    def add_playlist(self):
        url = self.url_entry.get()
        self.player.set_playlist(url)
        self.destroy()
