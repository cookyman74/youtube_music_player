import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import pygame
from mutagen import File
from mutagen.easyid3 import EasyID3
from audio_waveform_visualizer import AudioWaveformVisualizer, RealTimeWaveformUpdater
import yt_dlp
import ffmpeg
from database_manager import DatabaseManager
from ytbList_player import YtbListPlayer

# 메인 GUI 음악 플레이어 클래스
class ModernPurplePlayer(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 테마 설정
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Custom colors
        self.purple_dark = "#1E1B2E"
        self.purple_mid = "#2D2640"
        self.purple_light = "#6B5B95"
        self.pink_accent = "#FF4B8C"

        # Window setup
        self.title("Music Player")
        self.geometry("400x600")
        self.configure(fg_color=self.purple_dark)
        self.playlist = []

        # DatabaseManager 초기화
        self.db_manager = DatabaseManager()

        # YtbListPlayer 초기화 및 DB에서 플레이리스트 로드
        self.ytb_player = YtbListPlayer(self.db_manager)
        self.load_playlists_from_db()

        # UI 요소 생성
        # self.create_main_ui()



        # Initialize audio engine
        self.initialize_audio_engine()

        # 재생 상태 초기화.
        self.current_audio = None
        self.is_playing = False
        self.playlist = []
        self.current_index = -1
        # self.ytb_player = YtbListPlayer()

        # Create tabs
        self.create_tab_view()

        # Create main content area
        self.create_main_player()
        self.create_playlist_view()
        self.create_search_view()

        # Show default view (player)
        self.show_view("player")

        # Create bottom navigation
        self.create_bottom_nav()

        # Start the update loop for player
        self.update_player()

    def initialize_audio_engine(self):
        """Initialize the audio playback engine"""
        if not pygame.mixer.get_init():
            pygame.mixer.init()
            pygame.mixer.music.set_volume(0.5)

    def load_playlists_from_db(self):
        """데이터베이스에서 모든 플레이리스트와 트랙을 로드"""
        playlists = self.db_manager.get_all_playlists()
        for playlist_id, title, url in playlists:
            tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
            for track in tracks:
                track_info = {
                    'title': track[0],
                    'artist': track[1],
                    'thumbnail': track[2],
                    'url': track[3],
                    'path': track[4]
                }
                self.playlist.append(track_info)

    def add_youtube_playlist(self):
        """사용자로부터 YouTube 플레이리스트 URL을 입력받고 재생 목록 생성"""
        url = simpledialog.askstring("YouTube Playlist", "Enter YouTube Playlist URL:")
        if url:
            self.ytb_player.set_play_list(url)
            for video in self.ytb_player.play_list:
                audio_path = self.ytb_player.download_and_convert_audio(video['url'], video['title'])
                # 유효한 파일만 플레이리스트에 추가
                if audio_path:
                    self.playlist.append(
                        {'path': audio_path, 'metadata': {'title': video['title'], 'artist': 'YouTube'}})
            self.update_playlist_ui()
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
                self.play_current()

    def add_files(self):
        """로컬 음악 파일 추가"""
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")])
        self.add_to_playlist(files)

    def add_to_playlist(self, files):
        """플레이리스트에 파일 추가"""
        for file in files:
            self.playlist.append({
                'path': file,
                'metadata': self.get_audio_metadata(file)
            })
        self.update_playlist_ui()
        if self.current_index == -1 and self.playlist:
            self.current_index = 0
            self.play_current()

    def update_playlist_ui(self):
        """UI의 플레이리스트 업데이트"""
        # 플레이리스트 UI를 새로 고칩니다. 예를 들어, self.playlist 리스트를 기반으로 목록을 표시합니다.
        pass

    def create_tab_view(self):
        """Create top tab navigation with equal width buttons"""
        self.tab_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)
        self.tab_frame.pack(fill="x", padx=20, pady=10)

        # Configure grid columns with equal weight
        self.tab_frame.grid_columnconfigure(0, weight=1)
        self.tab_frame.grid_columnconfigure(1, weight=1)
        self.tab_frame.grid_columnconfigure(2, weight=1)

        # Updated tab names
        tabs = ["Menu", "Playlist", "Album"]
        self.tab_buttons = []

        # Create buttons with equal widths using grid
        for i, tab in enumerate(tabs):
            btn = ctk.CTkButton(
                self.tab_frame,
                text=tab,
                fg_color="transparent",
                text_color="gray",
                hover_color=self.purple_mid,
                command=lambda t=tab: self.select_tab(t)
            )
            btn.grid(row=0, column=i, sticky="ew", padx=2)
            self.tab_buttons.append(btn)

        # Set first tab as active
        self.tab_buttons[0].configure(fg_color=self.pink_accent, text_color="white")

    def create_main_player(self):
        """Create main player view"""
        self.player_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)

        # Album art
        self.album_frame = ctk.CTkFrame(self.player_frame, fg_color=self.purple_mid)
        self.album_frame.pack(pady=20, padx=20)
        self.load_album_art("default_album.png")

        # Initialize waveform visualizer
        self.wave_canvas = tk.Canvas(
            self.player_frame,
            height=60,
            bg=self.purple_dark,
            highlightthickness=0
        )
        self.wave_canvas.pack(fill="x", padx=20)

        self.waveform_visualizer = AudioWaveformVisualizer(
            self.wave_canvas,
            self.pink_accent,
            self.purple_dark
        )
        self.waveform_updater = RealTimeWaveformUpdater(
            self.waveform_visualizer,
            self
        )

        # Song info
        self.song_title_label = ctk.CTkLabel(
            self.player_frame,
            text="No song playing",
            font=("Helvetica", 20, "bold"),
            text_color="white"
        )
        self.song_title_label.pack(pady=(20, 0))

        self.artist_label = ctk.CTkLabel(
            self.player_frame,
            text="Artist",
            font=("Helvetica", 12),
            text_color="gray"
        )
        self.artist_label.pack()

        # Progress bar and time
        self.progress_frame = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=20, pady=10)

        self.time_current = ctk.CTkLabel(self.progress_frame, text="00:00")
        self.time_current.pack(side="left")
        self.time_total = ctk.CTkLabel(self.progress_frame, text="00:00")
        self.time_total.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        # Volume control
        self.volume_frame = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        self.volume_frame.pack(fill="x", padx=20)

        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            command=self.set_volume
        )
        self.volume_slider.pack(side="right", fill="x", expand=True, padx=10)
        self.volume_slider.set(50)

        volume_icon = ctk.CTkLabel(self.volume_frame, text="🔊")
        volume_icon.pack(side="left")

        # Control buttons
        self.controls_frame = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        self.controls_frame.pack(pady=20)

        controls = {
            "prev": ("⏮", self.play_previous),
            "play": ("▶", self.toggle_play),
            "next": ("⏭", self.play_next)
        }

        for control, (icon, command) in controls.items():
            btn = ctk.CTkButton(
                self.controls_frame,
                text=icon,
                width=40,
                height=40,
                fg_color=self.purple_mid if control == "play" else "transparent",
                hover_color=self.purple_light,
                command=command
            )
            btn.pack(side="left", padx=10)
            if control == "play":
                self.play_button = btn

    def load_album_art(self, path):
        """Load album art image"""
        try:
            if not os.path.exists('images'):
                os.makedirs('images')

            if not os.path.dirname(path):
                path = os.path.join('images', path)

            if os.path.exists(path):
                img = Image.open(path)
            else:
                img = Image.new('RGB', (200, 200), self.purple_light)

            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            photo = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 200))

            for widget in self.album_frame.winfo_children():
                widget.destroy()

            label = ctk.CTkLabel(self.album_frame, image=photo, text="")
            label.image = photo
            label.pack(fill="both", expand=True)

        except Exception as e:
            print(f"Error loading album art: {e}")
            for widget in self.album_frame.winfo_children():
                widget.destroy()

            placeholder = ctk.CTkLabel(
                self.album_frame,
                text="No Album Art",
                width=200,
                height=200,
                fg_color=self.purple_light
            )
            placeholder.pack(fill="both", expand=True)

    def create_playlist_view(self):
        """Create playlist view"""
        self.playlist_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)

        # Search bar
        search_frame = ctk.CTkFrame(self.playlist_frame, fg_color=self.purple_mid)
        search_frame.pack(fill="x", padx=20, pady=10)

        search_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_container.pack(fill="x", padx=10, pady=10)

        search_icon = ctk.CTkLabel(search_container, text="🔍", fg_color="transparent")
        search_icon.pack(side="left", padx=(5, 0))

        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="Search songs...",
            fg_color=self.purple_dark,
            border_color=self.purple_light,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.filter_playlist)

        self.playlist_container = ctk.CTkScrollableFrame(
            self.playlist_frame,
            fg_color=self.purple_dark,
        )
        self.playlist_container.pack(fill="both", expand=True, padx=20, pady=10)

        self.song_frames = []
        self.update_playlist_ui()

    def create_search_view(self):
        """Create search view"""
        self.search_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)

        ctk.CTkLabel(
            self.search_frame,
            text="Top Playlists",
            font=("Helvetica", 20, "bold")
        ).pack(anchor="w", padx=20, pady=20)

        for i in range(2):
            playlist_item = ctk.CTkFrame(
                self.search_frame,
                fg_color=self.purple_mid
            )
            playlist_item.pack(fill="x", padx=20, pady=5)

            ctk.CTkLabel(
                playlist_item,
                text=f"Playlist {i + 1}",
                font=("Helvetica", 14, "bold")
            ).pack(anchor="w", padx=10, pady=10)

    def create_bottom_nav(self):
        """Create bottom navigation bar"""
        nav_frame = ctk.CTkFrame(self, fg_color=self.purple_mid, height=50)
        nav_frame.pack(side="bottom", fill="x")

        for icon in ["🏠", "📃", "🔍"]:
            btn = ctk.CTkButton(
                nav_frame,
                text=icon,
                width=30,
                fg_color="transparent",
                hover_color=self.purple_light,
                command=lambda i=icon: self.navigate(i)
            )
            btn.pack(side="left", expand=True)

    def select_tab(self, tab):
        """Handle tab selection"""
        # Update tab button appearances
        for btn in self.tab_buttons:
            if btn.cget("text") == tab:
                btn.configure(fg_color=self.pink_accent, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="gray")

        # Hide all frames first
        frames_to_hide = [
            self.player_frame,
            self.playlist_frame,
            self.search_frame,
            getattr(self, 'menu_frame', None),
            getattr(self, 'album_grid_frame', None)
        ]

        for frame in frames_to_hide:
            if frame:
                frame.pack_forget()

        # Show selected view
        if tab == "Menu":
            self.show_menu_view()
        elif tab == "Playlist":
            self.playlist_frame.pack(fill="both", expand=True)
        elif tab == "Album":
            self.show_album_view()

    def show_menu_view(self):
        """Show menu options"""
        for frame in [self.player_frame, self.playlist_frame, self.search_frame]:
            frame.pack_forget()

        if not hasattr(self, 'menu_frame'):
            self.menu_frame = ctk.CTkFrame(self, fg_color="#1E1B2E")
            options = [
                ("Add Music Files", "🎵"),
                ("Add YouTube Playlist", "▶️"),
                ("Set Playlist Directory", "📁"),
                ("Settings", "⚙️"),
                ("About", "ℹ️")
            ]
            for text, icon in options:
                option_frame = ctk.CTkFrame(self.menu_frame, fg_color="#2D2640", corner_radius=10)
                option_frame.pack(fill="x", padx=20, pady=5)
                btn = ctk.CTkButton(option_frame, text=f"{icon} {text}", fg_color="transparent", hover_color="#6B5B95",
                                    anchor="w", command=lambda t=text: self.handle_menu_option(t))
                btn.pack(fill="x", padx=10, pady=10)
        self.menu_frame.pack(fill="both", expand=True)

        self.menu_frame.pack(fill="both", expand=True)

    def handle_menu_option(self, option):
        """Handle menu option selection"""
        if option == "Add Music Files":
            self.add_files()
        elif option == "Add YouTube Playlist":
            self.add_youtube_playlist()
        elif option == "Set Playlist Directory":
            directory = filedialog.askdirectory()
            if directory:
                audio_files = []
                for file in os.listdir(directory):
                    if file.endswith(('.mp3', '.wav', '.ogg')):
                        audio_files.append(os.path.join(directory, file))
                self.add_to_playlist(audio_files)
        elif option == "Settings":
            self.show_settings()
        elif option == "About":
            self.show_about()

    def show_album_view(self):
        """Show album grid view"""
        for frame in [self.player_frame, self.playlist_frame, self.search_frame,
                      self.menu_frame if hasattr(self, 'menu_frame') else None]:
            if frame:
                frame.pack_forget()

        if not hasattr(self, 'album_grid_frame'):
            self.album_grid_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)

            search_frame = ctk.CTkFrame(self.album_grid_frame, fg_color=self.purple_mid)
            search_frame.pack(fill="x", padx=20, pady=10)

            ctk.CTkEntry(
                search_frame,
                placeholder_text="Search Albums...",
                fg_color=self.purple_dark,
                border_color=self.purple_light
            ).pack(fill="x", padx=10, pady=10)

            album_container = ctk.CTkScrollableFrame(
                self.album_grid_frame,
                fg_color=self.purple_dark
            )
            album_container.pack(fill="both", expand=True, padx=20)

        self.album_grid_frame.pack(fill="both", expand=True)

    def show_view(self, view):
        """Show selected view and hide others"""
        # Hide all frames
        frames_to_hide = [
            self.player_frame,
            self.playlist_frame,
            self.search_frame,
            getattr(self, 'menu_frame', None),
            getattr(self, 'album_grid_frame', None)
        ]

        for frame in frames_to_hide:
            if frame:
                frame.pack_forget()

        # Show selected frame
        if view == "player":
            self.player_frame.pack(fill="both", expand=True)
        elif view == "playlist":
            self.playlist_frame.pack(fill="both", expand=True)
        elif view == "search":
            self.search_frame.pack(fill="both", expand=True)

    def navigate(self, icon):
        """Handle bottom navigation"""
        # Hide all frames first
        frames_to_hide = [
            self.player_frame,
            self.playlist_frame,
            self.search_frame,
            getattr(self, 'menu_frame', None),
            getattr(self, 'album_grid_frame', None)
        ]

        for frame in frames_to_hide:
            if frame:
                frame.pack_forget()

        # Show selected view
        if icon == "🏠":
            self.player_frame.pack(fill="both", expand=True)
        elif icon == "📃":
            self.playlist_frame.pack(fill="both", expand=True)
        elif icon == "🔍":
            self.search_frame.pack(fill="both", expand=True)

    def add_to_playlist(self, files):
        """Add files to playlist and update UI"""
        for file in files:
            self.playlist.append({
                'path': file,
                'metadata': self.get_audio_metadata(file)
            })
        self.update_playlist_ui()

        # If this is the first song added, start playing
        if self.current_index == -1 and self.playlist:
            self.current_index = 0
            self.play_current()

    def get_audio_metadata(self, file_path):
        """Extract metadata from audio file"""
        try:
            audio = EasyID3(file_path)
            return {
                'title': audio.get('title', ['Unknown Title'])[0],
                'artist': audio.get('artist', ['Unknown Artist'])[0],
                'album': audio.get('album', ['Unknown Album'])[0]
            }
        except:
            # If EasyID3 fails, use filename as title
            return {
                'title': os.path.splitext(os.path.basename(file_path))[0],
                'artist': 'Unknown Artist',
                'album': 'Unknown Album'
            }

    def update_playlist_ui(self):
        """UI의 플레이리스트 업데이트"""
        for frame in self.song_frames:
            frame.destroy()
        self.song_frames.clear()
        for i, song in enumerate(self.playlist):
            song_frame = ctk.CTkFrame(self.playlist_container, fg_color="#2D2640", corner_radius=10)
            song_frame.pack(fill="x", pady=5)
            self.song_frames.append(song_frame)
            info_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=10)
            play_btn = ctk.CTkButton(info_frame, text="▶", width=30, fg_color="transparent", hover_color="#6B5B95",
                                     command=lambda idx=i: self.play_selected(idx))
            play_btn.pack(side="left", padx=(0, 10))
            metadata = song['metadata']
            title_label = ctk.CTkLabel(info_frame, text=metadata['title'], font=("Helvetica", 14, "bold"), anchor="w")
            title_label.pack(fill="x", pady=(0, 2))
            artist_label = ctk.CTkLabel(info_frame, text=metadata['artist'], font=("Helvetica", 12), text_color="gray",
                                        anchor="w")
            artist_label.pack(fill="x")

    def filter_playlist(self, event=None):
        """Filter playlist based on search entry"""
        search_term = self.search_entry.get().lower()

        # Clear existing song frames
        for frame in self.song_frames:
            frame.destroy()
        self.song_frames.clear()

        # Add filtered songs to playlist
        for i, song in enumerate(self.playlist):
            metadata = song['metadata']
            if (search_term in metadata['title'].lower() or
                    search_term in metadata['artist'].lower()):
                song_frame = ctk.CTkFrame(
                    self.playlist_container,
                    fg_color=self.purple_mid,
                    corner_radius=10
                )
                song_frame.pack(fill="x", pady=5)
                self.song_frames.append(song_frame)

                # Song info container
                info_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=10)

                # Play button
                play_btn = ctk.CTkButton(
                    info_frame,
                    text="▶",
                    width=30,
                    fg_color="transparent",
                    hover_color=self.purple_light,
                    command=lambda idx=i: self.play_selected(idx)
                )
                play_btn.pack(side="left", padx=(0, 10))

                # Song details
                title_label = ctk.CTkLabel(
                    info_frame,
                    text=metadata['title'],
                    font=("Helvetica", 14, "bold"),
                    anchor="w"
                )
                title_label.pack(fill="x", pady=(0, 2))

                artist_label = ctk.CTkLabel(
                    info_frame,
                    text=metadata['artist'],
                    font=("Helvetica", 12),
                    text_color="gray",
                    anchor="w"
                )
                artist_label.pack(fill="x")

    def play_selected(self, index):
        """Play selected song from playlist"""
        self.current_index = index
        self.play_current()

    def play_current(self):
        """Play the current track"""
        if 0 <= self.current_index < len(self.playlist):
            current_track = self.playlist[self.current_index]

            try:
                pygame.mixer.music.load(current_track['path'])
                pygame.mixer.music.play()
                self.is_playing = True
                self.play_button.configure(text="⏸")
                self.update_song_info(current_track)

                # Start waveform visualization
                if self.waveform_visualizer:
                    self.waveform_updater.start_update()
            except Exception as e:
                print(f"Error playing file: {e}")

    def toggle_play(self):
        """Toggle between play and pause"""
        if self.current_index >= 0:
            if self.is_playing:
                pygame.mixer.music.pause()
                self.play_button.configure(text="▶")
            else:
                pygame.mixer.music.unpause()
                self.play_button.configure(text="⏸")
            self.is_playing = not self.is_playing

    def play_next(self):
        """Play next track in playlist"""
        if self.playlist:
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_current()

    def play_previous(self):
        """Play previous track in playlist"""
        if self.playlist:
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_current()

    def set_volume(self, value):
        """Set playback volume"""
        pygame.mixer.music.set_volume(float(value) / 100)

    def update_player(self):
        """Update player UI elements"""
        if self.is_playing:
            try:
                current_pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
                if current_pos > 0:
                    self.progress_bar.set(current_pos / self.get_audio_length())
                    self.time_current.configure(text=self.format_time(current_pos))
            except:
                pass

        # Schedule next update
        self.after(100, self.update_player)

    def get_audio_length(self):
        """Get length of current audio file"""
        if self.current_index >= 0:
            try:
                audio = File(self.playlist[self.current_index]['path'])
                return audio.info.length
            except:
                return 0
        return 0

    def format_time(self, seconds):
        """Format time in seconds to MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def show_settings(self):
        """Show settings window"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("300x200")
        settings_window.configure(fg_color=self.purple_dark)
        # Add settings options here

    def show_about(self):
        """Show about window"""
        about_window = ctk.CTkToplevel(self)
        about_window.title("About")
        about_window.geometry("300x200")
        about_window.configure(fg_color=self.purple_dark)

        ctk.CTkLabel(
            about_window,
            text="Modern Purple Music Player",
            font=("Helvetica", 16, "bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            about_window,
            text="Version 1.0",
            font=("Helvetica", 12)
        ).pack()

        ctk.CTkLabel(
            about_window,
            text="© 2024 Your Name",
            font=("Helvetica", 12)
        ).pack(pady=10)

if __name__ == "__main__":
    app = ModernPurplePlayer()
    app.mainloop()