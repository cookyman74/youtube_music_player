# player/app.py
import tkinter as tk
from tkinter import ttk
from player.ytb_list_player import YtbListPlayer
from player.components.playlist_popup import PlaylistPopup
from player.components.control_panel import ControlPanel

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modern Music Player")
        self.geometry("800x600")
        self.configure(bg="#282828")

        self.player = YtbListPlayer()
        self.create_widgets()

    def create_widgets(self):
        # Playlist Registration Button
        playlist_button = tk.Button(self, text="Register Playlist", command=self.open_playlist_popup)
        playlist_button.pack(pady=10)

        # Control Panel (Play, Pause, Next, Prev)
        control_panel = ControlPanel(self, self.player)
        control_panel.pack(side="bottom", pady=20)

    def open_playlist_popup(self):
        PlaylistPopup(self, self.player)

    def load_playlist(self, url):
        self.player.set_playlist(url)
        self.refresh_playlist()

    def refresh_playlist(self):
        # Refresh playlist display (e.g., update track list view)
        pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
