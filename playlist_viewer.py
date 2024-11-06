import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import os

from customtkinter import CTkImage


class PlaylistViewer(ctk.CTkFrame):
    def __init__(self, parent, db_manager, main_app, playlist_id=None):
        super().__init__(parent)

        self.parent = parent
        self.db_manager = db_manager
        self.main_app = main_app
        self.playlist_id = playlist_id
        self.current_mode = None  # 'all' or 'playlist'
        self.filtered_tracks = []  # 필터링된 트랙 리스트

        # 페이징 관련 변수
        self.page = 1
        self.items_per_page = 20
        self.is_loading = False
        self.has_more = True
        self.all_tracks = []
        self.current_tracks = []

        # UI 색상 테마
        self.purple_dark = "#1E1B2E"
        self.purple_mid = "#2D2640"
        self.purple_light = "#6B5B95"
        self.pink_accent = "#FF4B8C"

        self.setup_ui()

    def setup_ui(self):
        """플레이리스트 뷰어 UI 구성"""
        self.configure(fg_color=self.purple_dark)

        # 헤더 프레임 (모드 표시)
        self.header_frame = ctk.CTkFrame(self, fg_color=self.purple_mid)
        self.header_frame.pack(fill="x", padx=20, pady=(10, 0))

        self.mode_label = ctk.CTkLabel(
            self.header_frame,
            text="",
            font=("Helvetica", 16, "bold")
        )
        self.mode_label.pack(pady=10)

        # 검색바 프레임
        self.create_search_bar()

        # 트랙 리스트 컨테이너
        self.create_track_list()

        # # 트랙 목록 로드
        # if self.playlist_id:
        #     self.load_tracks(self.playlist_id)

        # 로딩 인디케이터
        self.loading_label = ctk.CTkLabel(
            self,
            text="로딩 중...",
            text_color="gray",
            font=("Helvetica", 12)
        )

    def show_all_tracks(self):
        """모든 트랙 표시 모드"""
        try:
            self.current_mode = 'all'
            self.mode_label.configure(text="전체 트랙 목록")

            # 트랙 리스트 초기화
            self.clear_tracks()

            # 모든 트랙 로드
            tracks = []
            playlists = self.db_manager.get_all_playlists()
            for playlist_id, _, _ in playlists:
                playlist_tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
                tracks.extend(playlist_tracks)

            self.all_tracks = tracks
            self.filtered_tracks = tracks.copy()  # 초기 필터링된 트랙은 전체 트랙

            # 검색창 초기화
            if hasattr(self, 'search_entry'):
                self.search_entry.delete(0, 'end')

            # 트랙 표시
            self.load_filtered_tracks()

        except Exception as e:
            messagebox.showerror("Error", f"전체 트랙 표시 중 오류 발생: {e}")

    def show_playlist_tracks(self, playlist_id):
        """특정 플레이리스트의 트랙 표시 모드"""
        try:
            self.current_mode = 'playlist'

            # 플레이리스트 정보 가져오기
            playlist = self.db_manager.get_playlist_by_id(playlist_id)
            if playlist:
                self.mode_label.configure(text=f"앨범: {playlist[1]}")

            # 트랙 리스트 초기화
            self.clear_tracks()

            # 트랙 로드
            self.all_tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
            self.filtered_tracks = self.all_tracks.copy()  # 초기 필터링된 트랙은 전체 트랙

            # 검색창 초기화
            if hasattr(self, 'search_entry'):
                self.search_entry.delete(0, 'end')

            # 트랙 표시
            self.load_filtered_tracks()

        except Exception as e:
            messagebox.showerror("Error", f"플레이리스트 표시 중 오류 발생: {e}")

    def clear_tracks(self):
        """트랙 리스트 초기화"""
        # 기존 트랙 카드 제거
        for widget in self.track_container.winfo_children():
            widget.destroy()

        # 페이징 변수 초기화
        self.page = 1
        self.has_more = True
        self.all_tracks = []
        self.current_tracks = []

    def load_all_tracks(self):
        """모든 트랙 로드"""
        try:
            # 모든 플레이리스트의 트랙 가져오기
            tracks = []
            playlists = self.db_manager.get_all_playlists()
            for playlist_id, _, _ in playlists:
                playlist_tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
                tracks.extend(playlist_tracks)

            self.all_tracks = tracks
            self.load_more_tracks()

        except Exception as e:
            messagebox.showerror("Error", f"트랙 로드 중 오류 발생: {e}")

    def load_playlist_tracks(self, playlist_id):
        """특정 플레이리스트의 트랙 로드"""
        try:
            tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
            self.all_tracks = tracks
            self.load_more_tracks()

        except Exception as e:
            messagebox.showerror("Error", f"트랙 로드 중 오류 발생: {e}")

    def create_search_bar(self):
        """검색바 생성"""
        search_frame = ctk.CTkFrame(self, fg_color=self.purple_mid)
        search_frame.pack(fill="x", padx=20, pady=10)

        search_container = ctk.CTkFrame(search_frame, fg_color="transparent")
        search_container.pack(fill="x", padx=10, pady=10)

        # 검색 아이콘
        search_icon = ctk.CTkLabel(search_container, text="🔍", fg_color="transparent")
        search_icon.pack(side="left", padx=(5, 0))

        self.search_entry = ctk.CTkEntry(
            search_container,
            placeholder_text="트랙 검색...",
            fg_color=self.purple_dark,
            border_color=self.purple_light
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.search_entry.bind('<KeyRelease>', self.filter_tracks)

    def filter_tracks(self, event=None):
        """트랙 검색 필터링"""
        try:
            search_term = self.search_entry.get().lower()

            # 기존 트랙 카드 제거
            for widget in self.track_container.winfo_children():
                widget.destroy()

            # 검색어가 비어있으면 전체 트랙 표시
            if not search_term:
                self.filtered_tracks = self.all_tracks
            else:
                # 제목 또는 아티스트로 필터링
                self.filtered_tracks = [
                    track for track in self.all_tracks
                    if search_term in track[0].lower() or  # title
                       search_term in track[1].lower()     # artist
                ]

            # 페이징 변수 초기화
            self.page = 1
            self.has_more = True
            self.current_tracks = []

            # 필터링된 결과 표시
            self.load_filtered_tracks()

        except Exception as e:
            messagebox.showerror("Error", f"트랙 필터링 중 오류 발생: {e}")

    def load_filtered_tracks(self):
        """필터링된 트랙 로드 및 표시"""
        try:
            if self.is_loading or not self.has_more:
                return

            self.is_loading = True
            if hasattr(self, 'loading_label'):
                self.loading_label.pack(pady=10)

            # 현재 페이지에 해당하는 트랙 범위 계산
            start_idx = (self.page - 1) * self.items_per_page
            end_idx = start_idx + self.items_per_page
            new_tracks = self.filtered_tracks[start_idx:end_idx]

            if not new_tracks:
                self.has_more = False
                if hasattr(self, 'loading_label'):
                    self.loading_label.pack_forget()
                return

            # 트랙 카드 생성
            for track in new_tracks:
                if track not in self.current_tracks:
                    self.current_tracks.append(track)
                    self.create_track_card(track)

            self.page += 1

        except Exception as e:
            messagebox.showerror("Error", f"필터링된 트랙 로드 중 오류 발생: {e}")

        finally:
            self.is_loading = False
            if hasattr(self, 'loading_label'):
                self.loading_label.pack_forget()

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

    def load_more_tracks(self):
        """추가 트랙 로드 및 UI에 표시"""
        try:
            if self.is_loading or not self.has_more:
                return

            self.is_loading = True
            if hasattr(self, 'loading_label'):
                self.loading_label.pack(pady=10)

            # 현재 페이지에 해당하는 트랙 범위 계산
            start_idx = (self.page - 1) * self.items_per_page
            end_idx = start_idx + self.items_per_page
            new_tracks = self.all_tracks[start_idx:end_idx]

            if not new_tracks:
                self.has_more = False
                if hasattr(self, 'loading_label'):
                    self.loading_label.pack_forget()
                return

            # 트랙 카드 생성
            for track in new_tracks:
                if track not in self.current_tracks:
                    self.current_tracks.append(track)
                    self.create_track_card(track)

            self.page += 1

        except Exception as e:
            messagebox.showerror("Error", f"트랙 로드 중 오류 발생: {e}")

        finally:
            self.is_loading = False
            if hasattr(self, 'loading_label'):
                self.loading_label.pack_forget()

            # 스크롤바 업데이트
            if hasattr(self, 'track_container'):
                self.track_container.update_idletasks()

    def create_track_card(self, track):
        """트랙 카드 UI 생성"""
        try:
            track_frame = ctk.CTkFrame(
                self.track_container,
                fg_color=self.purple_mid,
                corner_radius=10
            )
            track_frame.pack(fill="x", pady=5, padx=10)

            # 트랙 정보 프레임
            info_frame = ctk.CTkFrame(track_frame, fg_color="transparent")
            info_frame.pack(fill="x", padx=10, pady=10)

            # 썸네일 표시 (있는 경우)
            thumbnail_path = track[2]  # thumbnail path
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    thumbnail = self.load_thumbnail(thumbnail_path)
                    if thumbnail:
                        thumbnail_label = ctk.CTkLabel(
                            info_frame,
                            image=thumbnail,
                            text=""
                        )
                        thumbnail_label.image = thumbnail  # 참조 유지
                        thumbnail_label.pack(side="left", padx=(0, 10))
                except Exception as e:
                    print(f"썸네일 로드 실패: {e}")

            # 재생/다운로드 버튼
            file_path = track[4]  # file path
            if file_path and os.path.exists(file_path):
                play_btn = ctk.CTkButton(
                    info_frame,
                    text="▶",
                    width=30,
                    fg_color="transparent",
                    hover_color=self.purple_light,
                    command=lambda t=track: self.play_track(t)
                )
                play_btn.pack(side="left", padx=(0, 10))
            else:
                download_btn = ctk.CTkButton(
                    info_frame,
                    text="Download",
                    width=30,
                    fg_color="transparent",
                    hover_color=self.pink_accent,
                    command=lambda t=track: self.download_track(t)
                )
                download_btn.pack(side="left", padx=(0, 10))

            # 트랙 제목
            title_label = ctk.CTkLabel(
                info_frame,
                text=track[0],  # title
                font=("Helvetica", 14, "bold"),
                anchor="w"
            )
            title_label.pack(fill="x", pady=(0, 2))

            # 아티스트 정보
            artist_label = ctk.CTkLabel(
                info_frame,
                text=track[1],  # artist
                font=("Helvetica", 12),
                text_color="gray",
                anchor="w"
            )
            artist_label.pack(fill="x")

        except Exception as e:
            print(f"트랙 카드 생성 중 오류 발생: {e}")

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
            image = image.resize((80, 80), Image.LANCZOS)  # 썸네일 크기 조정
            ctk_image = CTkImage(light_image=image, size=(80, 80))  # CTkImage로 변환
            return ctk_image
        except Exception as e:
            print(f"썸네일 로드 실패: {path} - {e}")
            return None



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
            # 현재 모든 트랙 정보와 함께 재생 요청
            self.main_app.play_selected_track(track_info, self.all_tracks)
        except Exception as e:
            messagebox.showerror("Error", f"트랙 재생 중 오류 발생: {e}")

    def download_track(self, track):
        """트랙 다운로드"""
        try:
            self.main_app.start_track_download(track)
        except Exception as e:
            messagebox.showerror("Error", f"트랙 다운로드 중 오류 발생: {e}")