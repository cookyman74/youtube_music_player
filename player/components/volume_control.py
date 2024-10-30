# 볼륨 조절

# player/components/volume_control.py
import tkinter as tk


class VolumeControl(tk.Frame):
    def __init__(self, master, player):
        super().__init__(master)
        self.player = player
        self.create_widgets()

    def create_widgets(self):
        label = tk.Label(self, text="Volume")
        label.pack()

        self.volume_slider = tk.Scale(self, from_=0, to=1, resolution=0.1, orient="horizontal", command=self.set_volume)
        self.volume_slider.set(1.0)  # 기본 볼륨 100%
        self.volume_slider.pack()

    def set_volume(self, val):
        self.player.volume = float(val)  # YtbListPlayer의 볼륨 설정
