# player_view.py
import customtkinter as ctk
import tkinter as tk
from PIL import Image
from customtkinter import CTkImage

class PlayerView(ctk.CTkFrame):
    def __init__(self, master, controller):
        super().__init__(master)
        self.controller = controller
        self.setup_theme_colors()
        self.initialize_ui()

    def setup_theme_colors(self):
        """테마 색상 설정"""
        self.purple_dark = "#1E1B2E"
        self.purple_mid = "#2D2640"
        self.purple_light = "#6B5B95"
        self.pink_accent = "#FF4B8C"

    def update_progress_bar(self, value):
        """프로그레스바 업데이트"""
        self.progress_bar.set(value)
        current_time = self.controller.get_audio_length() * value
        self.time_current.configure(text=self.format_time(current_time))

    def update_song_info(self, title, artist):
        """곡 정보 업데이트"""
        self.song_title_label.configure(text=title)
        self.artist_label.configure(text=artist)

    def update_play_button_state(self, is_playing):
        """재생/일시정지 버튼 상태 업데이트"""
        self.play_button.configure(text="⏸" if is_playing else "▶")

    def bind_player_controls(self):
        """플레이어 컨트롤 이벤트 바인딩"""
        self.progress_bar.bind("<ButtonPress-1>", self.on_progress_click)
        self.play_button.configure(command=self.controller.toggle_play)
        self.next_button.configure(command=self.controller.next_track)
        self.prev_button.configure(command=self.controller.previous_track)
