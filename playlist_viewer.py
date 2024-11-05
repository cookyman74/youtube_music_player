import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import os


class PlaylistViewer(ctk.CTkFrame):
    def __init__(self, parent, db_manager, main_app, playlist_id=None):
        super().__init__(parent)

        self.parent = parent
        self.db_manager = db_manager
        self.main_app = main_app
        self.playlist_id = playlist_id

        # UI 색상 테마
        self.purple_dark = "#1E1B2E"
        self.purple_mid = "#2D2640"
        self.purple_light = "#6B5B95"
        self.pink_accent = "#FF4B8C"

        self.setup_ui()

    def setup_ui(self):
        """플레이리스트 뷰어 UI 구성"""
        self.configure(fg_color=self.purple_dark)

        # 검색바 프레임
        self.create_search_bar()

        # 트랙 리스트 컨테이너
        self.create_track_list()

        # 트랙 목록 로드
        if self.playlist_id:
            self.load_tracks(self.playlist_id)

    def create_search_bar(self):
        """검색바 생성"""
        search_frame = ctk.CTkFrame(self, fg_color=self.purple_mid)
        search_frame.pack(fill="x", padx=20, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="트랙 검색...",
            fg_color=self.purple_dark,
            border_color=self.purple_light
        )
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind('<KeyRelease>', self.filter_tracks)

    def create_track_list(self):
        """트랙 리스트 컨테이너 생성"""
        self.track_container = ctk.CTkScrollableFrame(
            self,
            fg_color=self.purple_dark
        )
        self.track_container.pack(fill="both", expand=True, padx=20)

    def load_tracks(self, playlist_id):
        """특정 플레이리스트의 트랙 목록 로드"""
        try:
            tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
            for track in tracks:
                self.create_track_card(track)
        except Exception as e:
            messagebox.showerror("Error", f"트랙 로드 중 오류 발생: {e}")

    def create_track_card(self, track):
        """개별 트랙 카드 생성"""
        track_frame = ctk.CTkFrame(self.track_container, fg_color=self.purple_mid, corner_radius=10)
        track_frame.pack(fill="x", pady=5)

        # 트랙 정보 프레임
        info_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)

        # 썸네일이 있는 경우 표시
        if track[2]:  # thumbnail
            try:
                thumbnail = self.load_thumbnail(track[2])
                if thumbnail:
                    thumbnail_label = ctk.CTkLabel(info_frame, image=thumbnail, text="")
                    thumbnail_label.image = thumbnail
                    thumbnail_label.pack(side="left", padx=(0, 10))
            except Exception as e:
                print(f"썸네일 로드 실패: {e}")

        # 재생/다운로드 버튼
        if track[4]:  # path exists
            play_btn = ctk.CTkButton(
                info_frame,
                text="▶",
                width=30,
                fg_color="transparent",
                hover_color=self.purple_light,
                command=lambda: self.play_track(track)
            )
            play_btn.pack(side="left", padx=(0, 10))
        else:
            download_btn = ctk.CTkButton(
                info_frame,
                text="Download",
                width=30,
                fg_color="transparent",
                hover_color=self.pink_accent,
                command=lambda: self.download_track(track)
            )
            download_btn.pack(side="left", padx=(0, 10))

        # 트랙 제목
        title_label = ctk.CTkLabel(
            info_frame,
            text=track[0],
            font=("Helvetica", 14, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 2))

        # 아티스트
        artist_label = ctk.CTkLabel(
            info_frame,
            text=track[1],
            font=("Helvetica", 12),
            text_color="gray",
            anchor="w"
        )
        artist_label.pack(fill="x")

    def refresh_view(self):
        """플레이리스트 뷰 새로고침"""
        try:
            # 기존 트랙 카드들 제거
            for widget in self.track_container.winfo_children():
                widget.destroy()

            # 검색창 초기화
            if hasattr(self, 'search_entry'):
                self.search_entry.delete(0, 'end')

            # 현재 선택된 플레이리스트가 있는 경우
            if self.playlist_id:
                self.load_tracks(self.playlist_id)
            else:
                # 전체 플레이리스트의 모든 트랙 로드
                playlists = self.db_manager.get_all_playlists()
                for playlist_id, _, _ in playlists:
                    tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
                    for track in tracks:
                        self.create_track_card(track)

        except Exception as e:
            messagebox.showerror("Error", f"플레이리스트 새로고침 중 오류 발생: {e}")

    def update_view(self, playlist_id=None):
        """특정 플레이리스트로 뷰 업데이트"""
        self.playlist_id = playlist_id
        self.refresh_view()

    def load_thumbnail(self, path):
        """썸네일 이미지 로드"""
        try:
            image = Image.open(path)
            image = image.resize((80, 80), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            print(f"썸네일 로드 실패: {e}")
            return None

    def filter_tracks(self, event=None):
        """트랙 검색 필터링"""
        search_term = self.search_entry.get().lower()

        # 기존 트랙 카드 제거
        for widget in self.track_container.winfo_children():
            widget.destroy()

        # 필터링된 트랙 표시
        tracks = self.db_manager.get_tracks_by_playlist(self.playlist_id)
        for track in tracks:
            if search_term in track[0].lower() or search_term in track[1].lower():
                self.create_track_card(track)

    def play_track(self, track):
        """트랙 재생"""
        try:
            track_info = {
                'title': track[0],
                'artist': track[1],
                'thumbnail': track[2],
                'url': track[3],
                'path': track[4]
            }
            self.main_app.play_selected_track(track_info)
        except Exception as e:
            messagebox.showerror("Error", f"트랙 재생 중 오류 발생: {e}")

    def download_track(self, track):
        """트랙 다운로드"""
        try:
            self.main_app.start_track_download(track)
        except Exception as e:
            messagebox.showerror("Error", f"트랙 다운로드 중 오류 발생: {e}")