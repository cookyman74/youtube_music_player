# 플레이리스트 목록 창

# player/components/playlist_view.py
import tkinter as tk
from tkinter import Listbox

class PlaylistView(tk.Frame):
    def __init__(self, master, player, track_list_view):
        super().__init__(master)
        self.player = player
        self.track_list_view = track_list_view  # Track List View와 연동
        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self, text="Playlists")
        label.pack()

        self.playlist_listbox = Listbox(self, width=30, height=10)
        self.playlist_listbox.pack()
        self.playlist_listbox.bind("<<ListboxSelect>>", self.on_select_playlist)

    def add_playlist(self, playlist_name):
        self.playlist_listbox.insert(tk.END, playlist_name)

    def on_select_playlist(self, event):
        selected_index = self.playlist_listbox.curselection()
        if selected_index:
            playlist_name = self.playlist_listbox.get(selected_index)
            # 여기에서 선택된 플레이리스트의 트랙을 트랙 리스트 창에 로드
            self.track_list_view.load_tracks(self.player.play_list)
