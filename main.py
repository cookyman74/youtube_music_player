import tkinter as tk
from io import BytesIO
from tkinter import ttk, filedialog, simpledialog
import customtkinter as ctk
import requests
from PIL import Image, ImageTk
import os
import pygame
from mutagen import File
from mutagen.easyid3 import EasyID3
from pytube.extract import playlist_id

from album_viewer import AlbumViewer
from audio_waveform_visualizer import AudioWaveformVisualizer, RealTimeWaveformUpdater
from database_manager import DatabaseManager
from playlist_viewer import PlaylistViewer
from ytbList_player import YtbListPlayer
from file_addmodal import FileAddModal
import asyncio
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from settings_view import SettingsView
from tkinter import messagebox

# 메인 GUI 음악 플레이어 클래스
class ModernPurplePlayer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.update_queue = queue.Queue()  # UI 업데이트를 위한 큐 생성
        self.after(100, self.check_for_updates)  # 큐를 주기적으로 확인하는 함수 호출

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
        self.filtered_playlist = []  # 필터링된 플레이리스트를 저장할 리스트 추가
        self.is_seeking = False  # 드래그 상태를 나타내는 속성

        # DatabaseManager 초기화
        self.db_manager = DatabaseManager()

        # YtbListPlayer 초기화 및 DB에서 플레이리스트 로드
        self.ytb_player = YtbListPlayer(self.db_manager)
        self.load_playlists_from_db()

        # Initialize audio engine
        self.initialize_audio_engine()

        # 재생 상태 초기화.
        self.current_audio = None
        self.is_playing = False
        self.playlist = []
        self.current_index = -1
        # self.ytb_player = YtbListPlayer()

        # 현재 선택된 플레이리스트 ID 초기화
        self.current_playlist_id = None

        # 뷰어 인스턴스 초기화
        self.album_viewer = None
        self.playlist_viewer = None

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
            pygame.mixer.music.set_endevent(pygame.USEREVENT)  # Track end event 설정

    def load_playlists_from_db(self):
        """데이터베이스에서 모든 플레이리스트와 트랙을 로드"""
        playlists = self.db_manager.get_all_playlists()
        for playlist_id, title, url in playlists:
            tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
            for track in tracks:
                # 파일 경로가 None이 아니면 절대 경로로 변환, 그렇지 않으면 None 그대로 유지
                file_path = track[4]
                if file_path:
                    file_path = os.path.abspath(file_path)

                track_info = {
                    'title': track[0],
                    'artist': track[1],
                    'thumbnail': track[2],
                    'url': track[3],
                    'path': file_path,
                }
                self.playlist.append(track_info)

    def check_for_updates(self):
        """Queue에서 업데이트가 있는지 확인하고 UI 갱신"""
        try:
            while True:
                update_func = self.update_queue.get_nowait()
                update_func()  # 큐에서 가져온 함수를 실행하여 UI 갱신
        except queue.Empty:
            pass
        finally:
            # 일정 시간마다 큐를 확인하여 업데이트가 있을 경우 UI 반영
            self.after(100, self.check_for_updates)

    def add_youtube_playlist(self):
        """사용자로부터 YouTube 플레이리스트 URL을 입력받고 비동기로 재생 목록 생성"""
        url = simpledialog.askstring("YouTube Playlist", "Enter YouTube Playlist URL:")
        if url:
            # 다운로드 작업을 별도의 스레드에서 시작
            download_thread = threading.Thread(target=self.download_playlist, args=(url,))
            download_thread.start()

    def download_playlist(self, url):
        """YouTube 플레이리스트를 다운로드하고 UI를 업데이트하는 메소드 (별도 스레드에서 실행)"""
        try:
            self.ytb_player.set_play_list(url)
            successful_downloads = 0
            total_videos = len(self.ytb_player.play_list)
            downloaded_tracks = []

            # 다운로드 작업 수행 및 UI 업데이트
            for video in self.ytb_player.play_list:
                audio_path = self.ytb_player.download_and_convert_audio(video['url'], video['album'], video['title'])

                # 유효한 파일만 저장
                if audio_path:
                    successful_downloads += 1
                    downloaded_tracks.append({
                        'path': audio_path,
                        'title': video['title'],
                        'artist': video.get('artist', 'YouTube')
                    })

            # UI 업데이트를 메인 스레드에서 실행
            def update_ui():
                # 현재 플레이리스트 뷰어가 있다면 새로고침
                if hasattr(self, 'playlist_viewer') and self.playlist_viewer:
                    self.playlist_viewer.refresh_view()

                # 다운로드 완료 메시지 표시
                messagebox.showinfo(
                    "플레이리스트 다운로드 완료",
                    f"플레이리스트 다운로드가 완료되었습니다.\n성공: {successful_downloads}/{total_videos}"
                )

            # 메인 스레드에서 UI 업데이트 실행
            self.after(0, update_ui)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", f"다운로드 중 오류 발생: {e}"))

    # def download_youtube_playlist(self, url):
    #     """YouTube 플레이리스트 URL로부터 재생 목록을 다운로드하고 UI에 실시간 업데이트"""
    #     self.ytb_player.set_play_list(url)
    #
    #     for video in self.ytb_player.play_list:
    #         # 각 곡을 다운로드
    #         audio_path = self.ytb_player.download_and_convert_audio(video['url'], video['album'], video['title'])
    #
    #         # 유효한 파일만 playlist에 추가
    #         if audio_path:
    #             self.playlist.append(
    #                 {'path': audio_path, 'metadata': {'title': video['title'], 'artist': 'YouTube'}}
    #             )
    #
    #             # 실시간 UI 업데이트를 큐에 추가
    #             self.update_queue.put(self.partial_update_playlist_ui)
    #
    #     # 모든 다운로드가 완료된 후 UI를 최종 갱신
    #     self.update_queue.put(self.update_playlist_ui)
    #
    #     # 첫 곡 재생 설정
    #     if self.current_index == -1 and self.playlist:
    #         self.current_index = 0
    #         self.play_current()

    def add_song_to_playlist(self, audio_path, title, artist):
        """UI에 곡을 추가하는 메소드"""
        try:
            self.playlist.append({
                'path': audio_path,
                'metadata': {'title': title, 'artist': artist}
            })

            # 플레이리스트 뷰어가 있다면 새로고침
            if hasattr(self, 'playlist_viewer') and self.playlist_viewer:
                self.playlist_viewer.refresh_view()

        except Exception as e:
            print(f"곡 추가 중 오류 발생: {e}")

    def partial_update_playlist_ui(self):
        """실시간으로 추가된 곡을 UI에 반영"""
        # 새로운 곡만 추가하는 방식으로 UI 업데이트
        song = self.playlist[-1]  # 방금 추가된 곡
        song_frame = ctk.CTkFrame(self.playlist_container, fg_color="#2D2640", corner_radius=10)
        song_frame.pack(fill="x", pady=5)
        self.song_frames.append(song_frame)

        info_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)

        # 파일 경로가 있는 경우 재생 버튼 표시, 없는 경우 다운로드 버튼 표시
        if song['path'] is not None:
            play_btn = ctk.CTkButton(
                info_frame,
                text="▶",
                width=30,
                fg_color="transparent",
                hover_color="#6B5B95",
                command=lambda idx=len(self.playlist) - 1: self.play_selected(idx)
            )
            play_btn.pack(side="left", padx=(0, 10))
        else:
            download_btn = ctk.CTkButton(
                info_frame,
                text="Download",
                width=30,
                fg_color="transparent",
                hover_color="#FF4B8C",
                command=lambda s=song, frame=song_frame: self.start_download(s, frame)
            )
            download_btn.pack(side="left", padx=(0, 10))

        # 데이터베이스에서 가져온 트랙 정보를 사용하여 제목과 아티스트를 표시
        title_label = ctk.CTkLabel(
            info_frame,
            text=song['metadata']['title'],
            font=("Helvetica", 14, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 2))

        artist_label = ctk.CTkLabel(
            info_frame,
            text=song['metadata']['artist'],
            font=("Helvetica", 12),
            text_color="gray",
            anchor="w"
        )
        artist_label.pack(fill="x")

    def open_file_add_modal(self):
        """Open File Add Modal to add local music files to playlist."""
        FileAddModal(self, self.on_save_group)

    def on_save_group(self, group_name, files):
        """Handle files added from FileAddModal."""
        # Store files and group name in the database
        playlist_id = self.db_manager.add_playlist(group_name, 'local_file')  # Create playlist with group name

        for file_path in files:
            metadata = self.get_audio_metadata(file_path)
            title = metadata.get('title')
            artist = metadata.get('artist')
            thumbnail = metadata.get('thumbnail', None)  # Adjust as per your thumbnail logic

            self.db_manager.add_track(playlist_id, title, artist, thumbnail, 'local_file', file_path, 'file')  # URL is None

            # Add the song to the playlist UI
            self.playlist.append({
                'title': title,
                'artist': artist,
                'thumbnail': thumbnail,
                'url': 'file',
                'path': file_path
            })

        self.update_playlist_ui()  # Refresh UI

    def add_files(self):
        """로컬 음악 파일 추가"""
        self.open_file_add_modal()

    def get_or_create_local_playlist_id(self):
        """로컬 파일용 기본 플레이리스트 ID를 가져오거나 생성"""
        # "Local Files"라는 이름으로 로컬 파일 전용 플레이리스트를 생성하거나, 이미 존재하면 해당 ID를 가져옴
        local_playlist = self.db_manager.get_playlist_by_title("Local Files")
        if local_playlist:
            return local_playlist[0]  # 이미 존재하는 경우 ID 반환
        else:
            return self.db_manager.add_playlist("Local Files", None)  # 존재하지 않으면 새로 추가

    def get_audio_metadata(self, file_path):
        """오디오 파일에서 메타데이터 추출"""
        try:
            # 파일 형식을 자동으로 감지하여 메타데이터를 읽기
            audio = File(file_path, easy=True)
            return {
                'title': audio.get('title', ['Unknown Title'])[0],
                'artist': audio.get('artist', ['Unknown Artist'])[0],
                'album': audio.get('album', ['Unknown Album'])[0]
            }
        except:
            # EasyID3에서 실패 시 파일명을 기본 타이틀로 사용
            return {
                'title': os.path.splitext(os.path.basename(file_path))[0],
                'artist': 'Unknown Artist',
                'album': 'Unknown Album'
            }

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


    async def async_download(self, song, song_frame, loading_label):
        """비동기 다운로드 처리"""
        loop = asyncio.get_event_loop()

        # 다운로드 비동기 실행
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, self.download_audio, song)

        # 다운로드 성공 여부에 따라 UI 업데이트
        if result:
            self.update_playlist_ui()  # UI 갱신
        else:
            loading_label.destroy()  # 로딩바 제거 후 실패 메시지 표시
            download_btn = ctk.CTkButton(
                song_frame,
                text="Download",
                width=30,
                fg_color="transparent",
                hover_color="#FF4B8C",
                command=lambda s=song: self.start_download(s, song_frame)
            )
            download_btn.pack(side="left", padx=(0, 10))

            # 실패 메시지 표시
            error_label = ctk.CTkLabel(
                song_frame,
                text="Download failed. Try again.",
                font=("Helvetica", 10),
                text_color="red"
            )
            error_label.pack(fill="x", padx=(0, 10))

    def update_ui_after_download(self, result, song, song_frame, loading_label, download_btn):
        """다운로드 결과에 따라 UI 업데이트"""
        loading_label.pack_forget()  # 로딩바 제거

        if result:
            # 성공 시 UI 갱신
            self.update_playlist_ui()
        else:
            # 실패 시 Download 버튼과 오류 메시지 표시
            download_btn.pack(side="left", padx=(0, 10))  # 기존 Download 버튼 다시 표시

            error_label = ctk.CTkLabel(
                song_frame,
                text="Download failed. Try again.",
                font=("Helvetica", 10),
                text_color="red"
            )
            error_label.pack(fill="x", padx=(0, 10))

    def download_audio_thread(self, song, song_frame, loading_label, download_btn):
        """다운로드 작업을 별도 스레드에서 실행하고 UI 갱신"""
        # 다운로드 실행
        result = self.download_audio(song)

        # 메인 스레드에서 UI 업데이트
        self.playlist_container.after(
            0,
            lambda: self.update_ui_after_download(
                result,
                song,
                song_frame,
                loading_label,
                download_btn
            )
        )

        # 다운로드 결과에 따른 메시지 표시
        if result:
            self.playlist_container.after(0, lambda: messagebox.showinfo(
                "다운로드 완료",
                f"{song['title']} 다운로드가 완료되었습니다."
            ))

    def start_download(self, song, song_frame):
        """다운로드를 시작하고 로딩바를 표시"""
        # 기존 Download 버튼 찾기 및 숨기기
        existing_download_btn = song_frame.winfo_children()[0]
        existing_download_btn.pack_forget()  # 기존 Download 버튼 숨기기

        # 로딩 메시지 추가
        loading_label = ctk.CTkLabel(song_frame, text="Loading...", text_color="gray")
        loading_label.pack(side="left", padx=(0, 10))

        # 다운로드를 별도의 스레드에서 실행
        download_thread = threading.Thread(target=self.download_audio_thread,
                                           args=(song, song_frame, loading_label, existing_download_btn))
        download_thread.start()

    def update_playlist_ui(self, album_id=None):
        """UI의 플레이리스트를 최신 데이터로 업데이트"""
        # 기존 UI 요소 초기화
        for frame in self.song_frames:
            frame.destroy()
        self.song_frames.clear()

        # 데이터베이스에서 모든 트랙 정보 가져오기
        self.song_frames.clear()
        self.playlist.clear()

        if album_id is None:
            # 전체 플레이리스트를 가져오는 경우
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
        else:
            # 특정 앨범 ID에 해당하는 트랙만 가져오는 경우
            tracks = self.db_manager.get_tracks_by_playlist(album_id)
            for track in tracks:
                track_info = {
                    'title': track[0],
                    'artist': track[1],
                    'thumbnail': track[2],
                    'url': track[3],
                    'path': track[4]
                }
                self.playlist.append(track_info)

        for i, song in enumerate(self.playlist):
            song_frame = ctk.CTkFrame(self.playlist_container, fg_color="#2D2640", corner_radius=10)
            song_frame.pack(fill="x", pady=5)
            self.song_frames.append(song_frame)

            info_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=10)

            # Display the thumbnail if available
            if song.get('thumbnail'):
                thumbnail_label = ctk.CTkLabel(info_frame, image=self.load_thumbnail(song['thumbnail']))
                thumbnail_label.pack(side="left", padx=(0, 10))

            # 파일 경로가 있는 경우 재생 버튼 표시, 없는 경우 다운로드 버튼 표시
            if song['path'] is not None:
                play_btn = ctk.CTkButton(
                    info_frame,
                    text="▶",
                    width=30,
                    fg_color="transparent",
                    hover_color="#6B5B95",
                    command=lambda idx=i: self.play_selected(idx)
                )
                play_btn.pack(side="left", padx=(0, 10))
            else:
                download_btn = ctk.CTkButton(
                    info_frame,
                    text="Download",
                    width=30,
                    fg_color="transparent",
                    hover_color="#FF4B8C",
                    command=lambda s=song, frame=song_frame: self.start_download(s, frame)
                )
                download_btn.pack(side="left", padx=(0, 10))

            # 데이터베이스에서 가져온 트랙 정보를 사용하여 제목과 아티스트를 표시
            title_label = ctk.CTkLabel(
                info_frame,
                text=song['title'],
                font=("Helvetica", 14, "bold"),
                anchor="w"
            )
            title_label.pack(fill="x", pady=(0, 2))

            artist_label = ctk.CTkLabel(
                info_frame,
                text=song['artist'],
                font=("Helvetica", 12),
                text_color="gray",
                anchor="w"
            )
            artist_label.pack(fill="x")

    def load_thumbnail(self, thumbnail_path):
        """썸네일 파일 경로에서 이미지를 로드하여 CTkImage로 변환"""
        try:
            image = Image.open(thumbnail_path)
            image = image.resize((80, 80), Image.LANCZOS)  # 썸네일 크기 조정
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"썸네일 로딩 실패: {e}")
            return None  # 로딩 실패 시 None 반환

    def load_and_show_playlist(self, playlist_id):
        """특정 playlist_id에 해당하는 트랙을 로드하고 playlist 탭으로 이동"""
        try:
            # 현재 playlist_id 설정
            self.current_playlist_id = playlist_id

            # 탭 선택 및 UI 업데이트
            self.select_tab("Playlist")

            # PlaylistViewer가 없으면 생성
            if not self.playlist_viewer:
                self.playlist_viewer = PlaylistViewer(self, self.db_manager, self)

            # 특정 플레이리스트의 트랙 표시
            self.playlist_viewer.show_playlist_tracks(playlist_id)
            self.playlist_viewer.pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Error", f"플레이리스트 로드 중 오류 발생: {e}")

    def play_selected_track(self, track_info, all_tracks):
        """플레이리스트 뷰어에서 선택한 트랙 재생"""

        try:
            # 전체 플레이리스트 초기화 및 설정
            self.playlist.clear()

            # 현재 플레이리스트의 모든 트랙을 추가
            for track in all_tracks:
                self.playlist.append({
                    'title': track[0],
                    'artist': track[1],
                    'thumbnail': track[2],
                    'url': track[3],
                    'path': track[4]
                })

            # 선택한 트랙의 인덱스 찾기
            self.current_index = next(
                (i for i, track in enumerate(self.playlist)
                 if track['path'] == track_info['path']), 0
            )

            # 트랙 재생
            self.play_current()
            self.show_view("player")
        except Exception as e:
            messagebox.showerror("Error", f"트랙 재생 준비 중 오류 발생: {e}")

    def start_track_download(self, track):
        """트랙 다운로드 시작"""
        song = {
            'title': track[0],
            'url': track[3]
        }
        self.start_download(song, None)  # 두 번째 인자는 UI 업데이트용 frame

    def update_album_ui(self):
        """앨범(플레이리스트) UI 업데이트"""
        if not hasattr(self, 'album_grid_frame'):
            self.create_album_view()  # album_grid_frame이 없는 경우 초기화

        # UI 요소 초기화 및 기존 내용 제거
        for widget in self.album_grid_frame.winfo_children():
            widget.destroy()

        # 모든 플레이리스트를 데이터베이스에서 가져와 표시
        playlists = self.db_manager.get_all_playlists()
        for playlist_id, title, url in playlists:
            playlist_frame = ctk.CTkFrame(self.album_grid_frame, fg_color="#2D2640", corner_radius=10)
            playlist_frame.pack(fill="x", pady=5, padx=10)

            title_label = ctk.CTkLabel(playlist_frame, text=title, font=("Helvetica", 14, "bold"), anchor="w")
            title_label.pack(fill="x", padx=5, pady=(5, 0))

            url_label = ctk.CTkLabel(playlist_frame, text=url, font=("Helvetica", 12), text_color="gray", anchor="w")
            url_label.pack(fill="x", padx=5, pady=(0, 5))

            # 클릭 이벤트를 프레임과 라벨 모두에 바인딩
            playlist_frame.bind("<Button-1>", lambda e, pid=playlist_id: self.load_and_show_playlist(pid))
            title_label.bind("<Button-1>", lambda e, pid=playlist_id: self.load_and_show_playlist(pid))
            url_label.bind("<Button-1>", lambda e, pid=playlist_id: self.load_and_show_playlist(pid))

        self.album_grid_frame.update_idletasks()

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

    def create_album_view(self):
        """Album 뷰를 생성하고 album_grid_frame 초기화"""
        if not hasattr(self, 'album_viewer'):
            self.album_viewer = AlbumViewer(self, self.db_manager, self)
        return self.album_viewer

    def create_main_player(self):
        """Create main player view"""
        self.player_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)

        # Album art
        self.album_frame = ctk.CTkFrame(self.player_frame, fg_color=self.purple_mid)
        self.album_frame.pack(pady=20, padx=20)
        self.load_album_art("assets/images/album_default.png")

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

        # Progress bar 생성 및 이벤트 바인딩
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", pady=5)
        self.progress_bar.set(0)

        # Left-aligned current time label
        self.time_current = ctk.CTkLabel(self.progress_frame, text="00:00")
        self.time_current.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=5)  # progress bar의 왼쪽 끝에 위치

        # Right-aligned total time label
        self.time_total = ctk.CTkLabel(self.progress_frame, text="00:00")
        self.time_total.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=5)  # progress bar의 오른쪽 끝에 위치

        # Progress bar 이벤트 바인딩
        self.progress_bar.bind("<ButtonPress-1>", self.on_progress_click)
        self.progress_bar.bind("<B1-Motion>", self.on_progress_drag)
        self.progress_bar.bind("<ButtonRelease-1>", self.on_progress_release)

        ## Volume control
        # self.volume_frame = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        # self.volume_frame.pack(fill="x", padx=20)
        #
        # self.volume_slider = ctk.CTkSlider(
        #     self.volume_frame,
        #     from_=0,
        #     to=100,
        #     number_of_steps=100,
        #     command=self.set_volume
        # )
        # self.volume_slider.pack(side="right", fill="x", expand=True, padx=10)
        # self.volume_slider.set(100)
        #
        # volume_icon = ctk.CTkLabel(self.volume_frame, text="🔊")
        # volume_icon.pack(side="left")
        # volume_icon.pack(side="left")

        # Control buttons
        self.controls_frame = ctk.CTkFrame(self.player_frame, fg_color="transparent")
        self.controls_frame.pack(pady=15)

        controls = {
            "prev": ("⏮", self.play_previous),
            "play": ("▶", self.toggle_play),
            "next": ("⏭", self.play_next)
        }

        for control, (icon, command) in controls.items():
            btn = ctk.CTkButton(
                self.controls_frame,
                text=icon,
                width=60,
                height=60,
                fg_color=self.purple_mid if control == "play" else "transparent",
                hover_color=self.purple_light,
                font=("Helvetica", 20),
                command=command
            )
            btn.pack(side="left", padx=5)
            if control == "play":
                self.play_button = btn

    def on_progress_click(self, event):
        """Progress bar 클릭 이벤트 처리"""
        if self.current_index >= 0:
            self.is_seeking = True
            self.pause_visualization()
            self.seek_to_position(event)

    def pause_visualization(self):
        """파형 시각화 일시 중지"""
        if hasattr(self, 'waveform_updater') and self.waveform_updater:
            try:
                self.waveform_updater.stop_update()
            except Exception as e:
                print(f"Error pausing visualization: {e}")

    def on_progress_drag(self, event):
        """Progress bar 드래그 이벤트 처리"""
        if self.current_index >= 0 and self.is_seeking:
            self.seek_to_position(event)

    def on_progress_release(self, event):
        """Progress bar 릴리즈 이벤트 처리"""
        if self.current_index >= 0:
            self.seek_to_position(event)
            self.is_seeking = False
            self.resume_visualization()

    def resume_visualization(self):
        """파형 시각화 재개"""
        if hasattr(self, 'waveform_updater') and self.waveform_updater and self.is_playing:
            try:
                self.waveform_updater.start_update()
            except Exception as e:
                print(f"Error resuming visualization: {e}")

    def seek_to_position(self, event):
        """지정된 위치로 재생 위치 변경"""
        try:
            # 진행바 너비 대비 클릭 위치 계산
            width = self.progress_bar.winfo_width()
            relative_x = max(0, min(event.x, width))
            progress = relative_x / width

            # 전체 길이 및 새로운 위치 계산
            total_length = self.get_audio_length()
            new_position = total_length * progress

            # 현재 재생 상태 저장
            was_playing = self.is_playing

            # 재생 위치 변경
            if was_playing:
                pygame.mixer.music.stop()

            pygame.mixer.music.load(self.playlist[self.current_index]['path'])
            pygame.mixer.music.play(start=int(new_position))

            if not was_playing:
                pygame.mixer.music.pause()

            # UI 업데이트
            self.progress_bar.set(progress)
            self.time_current.configure(text=self.format_time(new_position))
            self.current_position = new_position

        except Exception as e:
            print(f"Seek error: {e}")

    def update_player(self):
        """플레이어 UI 업데이트"""
        if self.is_playing and not self.is_seeking:
            try:
                if pygame.mixer.music.get_busy():
                    current_pos = pygame.mixer.music.get_pos() / 1000
                    total_length = self.get_audio_length()

                    if current_pos > 0 and total_length > 0:
                        # 현재 위치가 전체 길이를 넘지 않도록 보정
                        current_pos = min(current_pos + self.current_position, total_length)
                        progress = current_pos / total_length

                        self.progress_bar.set(progress)
                        self.time_current.configure(text=self.format_time(current_pos))
                        self.time_total.configure(text=self.format_time(total_length))
                else:
                    # 현재 곡이 끝났으면 다음 곡 재생
                    self.play_next()

            except Exception as e:
                print(f"Update player error: {e}")

        self.after(50, self.update_player)

    def pause_waveform_update(self):
        """파형 시각화 업데이트 일시 중지"""
        if hasattr(self, 'waveform_updater'):
            self.waveform_updater.stop_update()

    def resume_waveform_update(self):
        """파형 시각화 업데이트 재개"""
        if hasattr(self, 'waveform_updater'):
            self.waveform_updater.start_update()

    def on_progress_bar_click(self, event):
        """Handle progress bar click to seek within the audio track"""
        if self.current_index >= 0:
            try:
                # 클릭한 위치의 비율 계산
                progress_width = self.progress_bar.winfo_width()
                click_position = max(0, min(1, event.x / progress_width))

                # 현재 재생 중이던 상태 저장
                was_playing = self.is_playing

                # 현재 트랙 다시 로드
                current_track = self.playlist[self.current_index]
                total_length = self.get_audio_length()
                new_position = click_position * total_length

                # 음악 다시 로드 및 재생
                pygame.mixer.music.load(current_track['path'])
                pygame.mixer.music.play(start=int(new_position))

                # 이전 상태가 일시정지였다면 다시 일시정지
                if not was_playing:
                    pygame.mixer.music.pause()
                    self.is_playing = False
                else:
                    self.is_playing = True

                # UI 업데이트
                self.progress_bar.set(click_position)
                self.time_current.configure(text=self.format_time(new_position))

            except Exception as e:
                print(f"Progress bar click error: {e}")

    def on_progress_bar_drag(self, event):
        """Handle progress bar drag to preview position"""
        if self.current_index >= 0:
            self.is_seeking = True
            progress_width = self.progress_bar.winfo_width()
            click_position = max(0, min(1, event.x / progress_width))

            # 미리보기 시간 표시
            preview_time = click_position * self.get_audio_length()
            self.progress_bar.set(click_position)
            self.time_current.configure(text=self.format_time(preview_time))

    def on_progress_bar_release(self, event):
        """Handle progress bar release to set new position"""
        if self.current_index >= 0:
            try:
                # 최종 위치 계산
                progress_width = self.progress_bar.winfo_width()
                click_position = max(0, min(1, event.x / progress_width))

                # 현재 재생 상태 저장
                was_playing = self.is_playing

                # 새로운 위치 계산
                total_length = self.get_audio_length()
                new_position = click_position * total_length

                # 트랙 다시 로드 및 재생
                current_track = self.playlist[self.current_index]
                pygame.mixer.music.load(current_track['path'])
                pygame.mixer.music.play(start=int(new_position))

                # 이전 상태 복원
                if not was_playing:
                    pygame.mixer.music.pause()
                    self.is_playing = False
                else:
                    self.is_playing = True

                # UI 업데이트
                self.progress_bar.set(click_position)
                self.time_current.configure(text=self.format_time(new_position))

            except Exception as e:
                print(f"Progress bar release error: {e}")
            finally:
                self.is_seeking = False


    def get_audio_length(self):
        """오디오 파일의 총 길이 반환"""
        if self.current_index >= 0 and self.current_index < len(self.playlist):
            try:
                audio = File(self.playlist[self.current_index]['path'])
                if hasattr(audio.info, 'length'):
                    return float(audio.info.length)
            except Exception as e:
                print(f"Error getting audio length: {e}")
        return 0.0


    # def on_progress_bar_drag_start(self, event):
    #     """사용자가 프로그레스바 드래그를 시작할 때 호출"""
    #     self.is_seeking = True
    #
    # def on_progress_bar_drag_end(self, event):
    #     """사용자가 프로그레스바 드래그를 끝낼 때 호출"""
    #     self.is_seeking = False
    #     # 사용자가 설정한 위치로 재생 위치 이동
    #     new_pos = self.progress_bar.get() * self.get_audio_length()
    #     pygame.mixer.music.play(start=new_pos)

    def load_album_art(self, path):
        """Load album art image"""
        try:
            # 기본 썸네일 경로 설정 (썸네일 디렉토리와 파일 경로가 올바르게 지정되어야 함)
            thumbnail_path = path if path and os.path.exists(path) else 'assets/images/album_default.jpg'

            # 이미지 로드 및 크기 조정
            img = Image.open(thumbnail_path)
            img = img.resize((200, 200), Image.LANCZOS)  # 메인 플레이어에서 사용할 크기

            # ImageTk.PhotoImage로 변환하여 CTkLabel에 표시
            photo = ImageTk.PhotoImage(img)

            # 이전 앨범 아트 이미지를 제거하고 새 이미지로 업데이트
            for widget in self.album_frame.winfo_children():
                widget.destroy()

            # CTkLabel에 이미지 추가
            label = ctk.CTkLabel(self.album_frame, image=photo, text="")
            label.image = photo  # 참조 유지
            label.pack(fill="both", expand=True)

        except Exception as e:
            print(f"앨범 아트 로딩 실패: {e}")
            # 실패 시 기본 이미지로 표시
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
        if not hasattr(self, 'playlist_viewer'):
            self.playlist_viewer = PlaylistViewer(self, self.db_manager, self)
        return self.playlist_viewer

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
        nav_frame = ctk.CTkFrame(self, fg_color=self.purple_mid, height=60)  # 상단바 높이와 비슷하게 설정
        nav_frame.pack(side="bottom", fill="x")

        for icon in ["🏠", "📃", "🔍"]:
            btn = ctk.CTkButton(
                nav_frame,
                text=icon,
                width=60,  # 버튼의 가로 크기를 더 크게 설정
                height=60,  # 버튼의 세로 크기를 더 크게 설정
                font=("Helvetica", 24),  # 아이콘 크기 조정을 위해 폰트 크기 설정
                fg_color="transparent",
                hover_color=self.purple_light,
                command=lambda i=icon: self.navigate(i)
            )
            btn.pack(side="left", expand=True)

    def hide_all_frames(self):
        """Hide all visible frames"""
        frames_to_hide = [
            self.player_frame,
            getattr(self, 'playlist_viewer', None),
            getattr(self, 'album_viewer', None),
            getattr(self, 'menu_frame', None)
        ]

        for frame in frames_to_hide:
            if frame and frame.winfo_exists():
                frame.pack_forget()

    def refresh_album_view(self):
        """앨범 뷰 새로고침"""
        if hasattr(self, 'album_viewer') and self.album_viewer:
            self.album_viewer.force_refresh()

    def show_selected_view(self, view):
        """Show the selected view"""
        try:
            if view == "Menu":
                self.show_menu_view()
            elif view == "Playlist":
                if not self.playlist_viewer:
                    self.playlist_viewer = PlaylistViewer(self, self.db_manager, self)

                if self.current_playlist_id:
                    # 선택된 앨범의 플레이리스트 표시
                    self.playlist_viewer.show_playlist_tracks(self.current_playlist_id)
                else:
                    # 선택된 앨범이 없으면 첫 번째 앨범 선택
                    playlists = self.db_manager.get_all_playlists()
                    if playlists:
                        self.current_playlist_id = playlists[0][0]
                        self.playlist_viewer.show_playlist_tracks(self.current_playlist_id)
                    else:
                        messagebox.showinfo("알림", "표시할 앨범이 없습니다.")

                self.playlist_viewer.pack(fill="both", expand=True)

            elif view == "Album":
                if not self.album_viewer:
                    self.album_viewer = AlbumViewer(self, self.db_manager, self)
                self.album_viewer.pack(fill="both", expand=True)
                self.album_viewer.refresh_view()
            elif view == "player":
                self.player_frame.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Error", f"뷰 전환 중 오류 발생: {e}")

    def set_current_playlist(self, playlist_id):
        """현재 선택된 플레이리스트 ID 설정"""
        self.current_playlist_id = playlist_id

    def select_tab(self, tab):
        """Handle tab selection"""
        # Update tab button appearances
        for btn in self.tab_buttons:
            if btn.cget("text") == tab:
                btn.configure(fg_color=self.pink_accent, text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color="gray")

        # Hide all frames first
        self.hide_all_frames()

        # Show selected view
        self.show_selected_view(tab)

    def show_menu_view(self):
        """Show menu options"""
        if not hasattr(self, 'menu_frame'):
            self.create_menu_frame()
        self.menu_frame.pack(fill="both", expand=True)

    def create_menu_frame(self):
        """Create menu frame with options"""
        self.menu_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)

        # 메뉴 옵션 정의
        menu_options = [
            {
                "text": "Add Music Files",
                "icon": "🎵",
                "command": self.add_files
            },
            {
                "text": "Add YouTube Playlist",
                "icon": "▶️",
                "command": self.add_youtube_playlist
            },
            # {
            #     "text": "Set Playlist Directory",
            #     "icon": "📁",
            #     "command": self.set_playlist_directory
            # },
            {
                "text": "Settings",
                "icon": "⚙️",
                "command": self.show_settings
            },
            {
                "text": "About",
                "icon": "ℹ️",
                "command": self.show_about
            }
        ]

        # 메뉴 옵션 버튼 생성
        for option in menu_options:
            self.create_menu_option(option)

    def create_menu_option(self, option):
        """Create individual menu option"""
        option_frame = ctk.CTkFrame(
            self.menu_frame,
            fg_color=self.purple_mid,
            corner_radius=10
        )
        option_frame.pack(fill="x", padx=20, pady=5)

        btn = ctk.CTkButton(
            option_frame,
            text=f"{option['icon']} {option['text']}",
            fg_color="transparent",
            hover_color=self.purple_light,
            anchor="w",
            command=option['command']
        )
        btn.pack(fill="x", padx=10, pady=10)

    # def set_playlist_directory(self):
    #     """Set playlist directory"""
    #     directory = filedialog.askdirectory()
    #     if directory:
    #         try:
    #             self.db_manager.save_setting('download_directory', directory)
    #             messagebox.showinfo("성공", "다운로드 디렉토리가 설정되었습니다.")
    #         except Exception as e:
    #             messagebox.showerror("Error", f"디렉토리 설정 중 오류 발생: {e}")

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

    # def show_album_view(self):
    #     """Show album grid view"""
    #     for frame in [self.player_frame, self.playlist_frame, self.search_frame,
    #                   self.menu_frame if hasattr(self, 'menu_frame') else None]:
    #         if frame:
    #             frame.pack_forget()
    #
    #     if not hasattr(self, 'album_grid_frame'):
    #         self.album_grid_frame = ctk.CTkFrame(self, fg_color=self.purple_dark)
    #
    #         search_frame = ctk.CTkFrame(self.album_grid_frame, fg_color=self.purple_mid)
    #         search_frame.pack(fill="x", padx=20, pady=10)
    #
    #         ctk.CTkEntry(
    #             search_frame,
    #             placeholder_text="Search Albums...",
    #             fg_color=self.purple_dark,
    #             border_color=self.purple_light
    #         ).pack(fill="x", padx=10, pady=10)
    #
    #         album_container = ctk.CTkScrollableFrame(
    #             self.album_grid_frame,
    #             fg_color=self.purple_dark
    #         )
    #         album_container.pack(fill="both", expand=True, padx=20)
    #
    #     self.album_grid_frame.pack(fill="both", expand=True)

    def show_view(self, view_name):
        """Show specific view"""
        self.hide_all_frames()
        self.show_selected_view(view_name)

    def navigate(self, icon):
        """Handle bottom navigation"""
        # Hide all frames first
        self.hide_all_frames()  # 기존의 hide_all_frames 메서드 재사용

        # Show selected view
        if icon == "🏠":
            self.player_frame.pack(fill="both", expand=True)
        elif icon == "📃": # 전체 플레이리스트 보기
            if not self.playlist_viewer:
                self.playlist_viewer = PlaylistViewer(self, self.db_manager, self)
            self.playlist_viewer.show_all_tracks()
            self.playlist_viewer.pack(fill="both", expand=True)
        elif icon == "🔍":
            if not self.album_viewer:
                self.album_viewer = AlbumViewer(self, self.db_manager, self)
            self.album_viewer.pack(fill="both", expand=True)
            self.album_viewer.refresh_view()

    def download_audio(self, song):
        """곡의 URL을 통해 오디오를 다운로드하고 파일 경로를 데이터베이스에 저장"""
        title = song['title']
        url = song['url']

        # YtbListPlayer 인스턴스를 사용하여 다운로드 및 변환
        audio_path = self.ytb_player.download_and_convert_audio(url, title)

        if audio_path:
            playlist_id = self.db_manager.get_playlist_id_by_url(url)
            if playlist_id is not None:
                self.db_manager.update_track_path(playlist_id, title, audio_path)
                song['path'] = audio_path  # 성공 시 경로 업데이트
                return True
            else:
                print("해당 URL에 대한 플레이리스트를 찾을 수 없습니다.")
        else:
            print("다운로드 실패: 파일을 다운로드할 수 없습니다.")

        return False  # 실패 시 False 반환

    def filter_playlist(self, event=None):
        """Filter playlist based on search entry"""
        search_term = self.search_entry.get().lower()

        # 기존 플레이리스트 UI 요소 초기화
        for frame in self.song_frames:
            frame.destroy()
        self.song_frames.clear()

        # 검색어에 따라 self.playlist에서 필터링된 곡들만 self.filtered_playlist에 저장
        self.filtered_playlist = [
            song for song in self.playlist
            if search_term in song.get('title', '').lower() or search_term in song.get('artist', '').lower()
        ]

        # 검색어에 따라 self.playlist에서 필터링된 곡들만 표시
        for i, song in enumerate(self.filtered_playlist):
            title = song.get('title', '').lower()
            artist = song.get('artist', '').lower()

            # 제목 또는 아티스트가 검색어를 포함하는 경우에만 표시
            if search_term in title or search_term in artist:
                song_frame = ctk.CTkFrame(self.playlist_container, fg_color="#2D2640", corner_radius=10)
                song_frame.pack(fill="x", pady=5)
                self.song_frames.append(song_frame)

                info_frame = ctk.CTkFrame(song_frame, fg_color="transparent")
                info_frame.pack(fill="x", padx=10, pady=10)

                # 파일 경로가 있는 경우 재생 버튼 표시, 없는 경우 다운로드 버튼 표시
                if song['path']:
                    play_btn = ctk.CTkButton(
                        info_frame,
                        text="▶",
                        width=30,
                        fg_color="transparent",
                        hover_color="#6B5B95",
                        command=lambda idx=i: self.play_selected(idx)
                    )
                    play_btn.pack(side="left", padx=(0, 10))
                else:
                    download_btn = ctk.CTkButton(
                        info_frame,
                        text="Download",
                        width=30,
                        fg_color="transparent",
                        hover_color="#FF4B8C",
                        command=lambda s=song, frame=song_frame: self.start_download(s, frame)
                    )
                    download_btn.pack(side="left", padx=(0, 10))

                # 곡 제목과 아티스트 정보 표시
                title_label = ctk.CTkLabel(
                    info_frame,
                    text=song['title'],
                    font=("Helvetica", 14, "bold"),
                    anchor="w"
                )
                title_label.pack(fill="x", pady=(0, 2))

                artist_label = ctk.CTkLabel(
                    info_frame,
                    text=song['artist'],
                    font=("Helvetica", 12),
                    text_color="gray",
                    anchor="w"
                )
                artist_label.pack(fill="x")

    def play_selected(self, index):
        """Play selected song from playlist"""
        self.current_index = index
        self.play_current()
        self.show_view("player")

    def play_current(self):
        """현재 트랙 재생"""
        if 0 <= self.current_index < len(self.playlist):
            try:
                current_track = self.playlist[self.current_index]
                file_path = current_track.get('path')

                if not file_path or not os.path.isfile(file_path):
                    print(f"Error: Invalid file path - {file_path}")
                    return

                # 오디오 재생
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                self.is_playing = True
                self.play_button.configure(text="⏸")
                self.current_position = 0.0

                # UI 업데이트
                if 'thumbnail' in current_track:
                    self.load_album_art(current_track['thumbnail'])
                self.update_song_info(current_track)

                # 파형 시각화 시작
                if hasattr(self, 'waveform_updater'):
                    self.waveform_updater.start_update()

                # 진행 시간 초기화
                total_length = self.get_audio_length()
                self.time_total.configure(text=self.format_time(total_length))
                self.progress_bar.set(0)

            except Exception as e:
                print(f"Error playing file: {e}")

    def toggle_play(self):
        """재생/일시정지 토글"""
        if self.current_index >= 0:
            if self.is_playing:
                pygame.mixer.music.pause()
                self.play_button.configure(text="▶")
                self.pause_visualization()
            else:
                pygame.mixer.music.unpause()
                self.play_button.configure(text="⏸")
                self.resume_visualization()
            self.is_playing = not self.is_playing

    def play_next(self):
        """다음 트랙 재생"""
        if self.playlist:
            # 현재 재생 중인 시각화 중지
            self.pause_visualization()
            # 다음 곡 인덱스로 변경
            self.current_index = (self.current_index + 1) % len(self.playlist)
            # 새로운 곡 재생
            self.play_current()

    def play_previous(self):
        """이전 트랙 재생"""
        if self.playlist:
            # 현재 재생 중인 시각화 중지
            self.pause_visualization()
            # 이전 곡 인덱스로 변경
            self.current_index = (self.current_index - 1) % len(self.playlist)
            # 새로운 곡 재생
            self.play_current()

    def set_volume(self, value):
        """Set playback volume"""
        pygame.mixer.music.set_volume(float(value) / 100)

    # def update_player(self):
    #     """Update player UI elements"""
    #     if self.is_playing and not self.is_seeking:  # 드래그 중이 아닐 때만 위치 업데이트
    #         try:
    #             current_pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
    #             if current_pos > 0:
    #                 self.progress_bar.set(current_pos / self.get_audio_length())
    #                 self.time_current.configure(text=self.format_time(current_pos))
    #         except:
    #             pass
    #
    #         # 재생 중인 곡이 끝났는지 확인하고 다음 곡으로 이동
    #     if not pygame.mixer.music.get_busy():  # 현재 곡이 끝난 상태
    #         self.play_next_in_filtered_playlist()
    #
    #         # Schedule next update
    #     self.after(100, self.update_player)

    def play_next_in_filtered_playlist(self):
        """Play the next song in the filtered playlist"""
        if self.filtered_playlist:
            self.current_index = (self.current_index + 1) % len(self.filtered_playlist)
            self.play_current()

    def update_song_info(self, track):
        """현재 재생 중인 곡의 정보를 UI에 업데이트합니다."""
        # 트랙 제목과 아티스트 정보를 업데이트
        title = track.get('title', 'Unknown Title')
        artist = track.get('artist', 'Unknown Artist')

        # 제목과 아티스트 라벨에 텍스트를 설정합니다.
        self.song_title_label.configure(text=title)
        self.artist_label.configure(text=artist)

    # def get_audio_length(self):
    #     """Get length of current audio file"""
    #     if self.current_index >= 0:
    #         try:
    #             audio = File(self.playlist[self.current_index]['path'])
    #             return audio.info.length
    #         except:
    #             return 0
    #     return 0

    def format_time(self, seconds):
        """Format time in seconds to MM:SS"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def get_album_count(self):
        """DatabaseManager를 통해 앨범 수를 가져옵니다."""
        return self.db_manager.get_album_count()

    def get_track_count(self):
        """DatabaseManager를 통해 트랙 수를 가져옵니다."""
        return self.db_manager.get_track_count()

    def show_settings(self):
        """Show settings window"""
        album_count = self.get_album_count()  # 앨범 수 계산
        track_count = self.get_track_count()  # 트랙 수 계산
        settings_window = SettingsView(self, self.db_manager, self.on_reset_settings, album_count, track_count)
        settings_window.grab_set()

    def on_reset_settings(self):
        """Reset settings callback"""
        # todo: 설정이 초기화되었을 때 UI를 업데이트하거나 추가적인 작업을 수행
        print("Settings have been reset.")
        # 예: 다운로드 위치 라벨을 초기화하거나 기타 UI 요소를 재설정
        self.update_ui_after_settings_reset()

    def update_ui_after_settings_reset(self):
        """Update UI elements after settings are reset"""
        # 설정 초기화 후 UI를 갱신하는 코드 작성
        # 예시: 다운로드 디렉토리 라벨 초기화
        if hasattr(self, 'download_directory_label'):
            self.download_directory_label.configure(text="Not Set")

        # 필요한 다른 UI 요소들을 갱신하거나 기본값으로 초기화하는 코드 추가
        # 예: 다운로드 정보 표시 초기화
        if hasattr(self, 'album_count_label'):
            self.album_count_label.configure(text="Albums downloaded: 0")

        if hasattr(self, 'track_count_label'):
            self.track_count_label.configure(text="Tracks downloaded: 0")

    def show_about(self):
        """Show about window"""
        about_window = ctk.CTkToplevel(self)
        about_window.title("About")
        about_window.geometry("300x200")
        about_window.configure(fg_color=self.purple_dark)

        ctk.CTkLabel(
            about_window,
            text="PyTube Player",
            font=("Helvetica", 16, "bold")
        ).pack(pady=20)

        ctk.CTkLabel(
            about_window,
            text="Version 1.0",
            font=("Helvetica", 12)
        ).pack()

        ctk.CTkLabel(
            about_window,
            text="© 2024 by cookyman",
            font=("Helvetica", 12)
        ).pack(pady=10)

if __name__ == "__main__":
    app = ModernPurplePlayer()
    app.mainloop()