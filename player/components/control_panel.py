# 재생/컨트롤 패널

# player/components/control_panel.py
import tkinter as tk


class ControlPanel(tk.Frame):
    def __init__(self, master, player):
        super().__init__(master)
        self.player = player
        self.create_widgets()

    def create_widgets(self):
        prev_button = tk.Button(self, text="<< Prev", command=self.player.prev_song)
        play_button = tk.Button(self, text="Play", command=lambda: self.player.load_and_play(self.player.current_index))
        stop_button = tk.Button(self, text="Stop", command=self.player.stop_song)
        next_button = tk.Button(self, text="Next >>", command=self.player.next_song)
        prev_button.pack(side="left")
        play_button.pack(side="left")
        stop_button.pack(side="left")
        next_button.pack(side="left")

        # Volume Control
        self.volume_control = tk.Scale(self, from_=0, to=1, resolution=0.1, orient="horizontal",
                                       command=self.set_volume)
        self.volume_control.pack(side="right", padx=20)

    def set_volume(self, val):
        self.player.volume = float(val)
