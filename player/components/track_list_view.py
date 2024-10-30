# 플레이리스트 내 음악 목록 창

# player/components/track_list_view.py
import tkinter as tk
from tkinter import Listbox

class TrackListView(tk.Frame):
    def __init__(self, master, player):
        super().__init__(master)
        self.player = player
        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self, text="Tracks")
        label.pack()

        self.track_listbox = Listbox(self, width=50, height=15)
        self.track_listbox.pack()
        self.track_listbox.bind("<<ListboxSelect>>", self.on_select_track)

    def load_tracks(self, tracks):
        """플레이리스트의 트랙 목록을 리스트박스에 표시"""
        self.track_listbox.delete(0, tk.END)  # 기존 목록 지우기
        for track in tracks:
            self.track_listbox.insert(tk.END, track['title'])

    def on_select_track(self, event):
        selected_index = self.track_listbox.curselection()
        if selected_index:
            self.player.load_and_play(selected_index[0])  # 선택한 트랙 재생
