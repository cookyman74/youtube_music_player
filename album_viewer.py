import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import os


class AlbumViewer(ctk.CTkFrame):
    def __init__(self, parent, db_manager, main_app):
        super().__init__(parent)

        self.parent = parent
        self.db_manager = db_manager
        self.main_app = main_app  # 메인 앱 참조

        # UI 색상 테마
        self.purple_dark = "#1E1B2E"
        self.purple_mid = "#2D2640"
        self.purple_light = "#6B5B95"
        self.pink_accent = "#FF4B8C"

        self.setup_ui()

    def setup_ui(self):
        """앨범 뷰어 UI 구성"""
        self.configure(fg_color=self.purple_dark)

        # 검색바 프레임
        self.create_search_bar()

        # 앨범 그리드 컨테이너
        self.create_album_grid()

        # 초기 앨범 목록 로드
        self.load_albums()

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
            placeholder_text="앨범 검색...",
            fg_color=self.purple_dark,
            border_color=self.purple_light
        )
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind('<KeyRelease>', self.filter_albums)

    def create_album_grid(self):
        """앨범 그리드 컨테이너 생성"""
        self.album_container = ctk.CTkScrollableFrame(
            self,
            fg_color=self.purple_dark
        )
        self.album_container.pack(fill="both", expand=True, padx=20)

    def refresh_view(self):
        """앨범 뷰 새로고침"""
        try:
            # 검색창 초기화
            if hasattr(self, 'search_entry'):
                self.search_entry.delete(0, 'end')

            # 기존 앨범 카드 제거
            for widget in self.album_container.winfo_children():
                widget.destroy()

            # 앨범 목록 다시 로드
            self.load_albums()

        except Exception as e:
            messagebox.showerror("Error", f"앨범 뷰 새로고침 중 오류 발생: {e}")

    def load_albums(self):
        """데이터베이스에서 앨범 목록 로드"""
        try:
            playlists = self.db_manager.get_all_playlists()
            for playlist_id, title, url in playlists:
                self.create_album_card(playlist_id, title, url)
        except Exception as e:
            messagebox.showerror("Error", f"앨범 로드 중 오류 발생: {e}")

    def create_album_card(self, playlist_id, title, url):
        """개별 앨범 카드 생성"""
        album_frame = ctk.CTkFrame(self.album_container, fg_color=self.purple_mid, corner_radius=10)
        album_frame.pack(fill="x", pady=5, padx=10)

        # 앨범 정보
        info_frame = ctk.CTkFrame(album_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)

        # 앨범 제목
        title_label = ctk.CTkLabel(
            info_frame,
            text=title,
            font=("Helvetica", 14, "bold"),
            anchor="w"
        )
        title_label.pack(fill="x", pady=(0, 2))

        # URL 표시 (있는 경우)
        if url:
            url_label = ctk.CTkLabel(
                info_frame,
                text=url,
                font=("Helvetica", 12),
                text_color="gray",
                anchor="w"
            )
            url_label.pack(fill="x")

        # 버튼 프레임
        button_frame = ctk.CTkFrame(album_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 10))

        # 앨범 수정 버튼
        ctk.CTkButton(
            button_frame,
            text="수정",
            width=60,
            fg_color=self.purple_light,
            command=lambda: self.edit_album(playlist_id)
        ).pack(side="left", padx=5)

        # 앨범 삭제 버튼
        ctk.CTkButton(
            button_frame,
            text="삭제",
            width=60,
            fg_color=self.pink_accent,
            command=lambda: self.delete_album(playlist_id)
        ).pack(side="left", padx=5)

        # 플레이리스트 보기 버튼
        ctk.CTkButton(
            button_frame,
            text="트랙 보기",
            width=80,
            fg_color=self.purple_light,
            command=lambda: self.view_playlist(playlist_id)
        ).pack(side="right", padx=5)

    def filter_albums(self, event=None):
        """앨범 검색 필터링"""
        search_term = self.search_entry.get().lower()

        # 기존 앨범 카드 제거
        for widget in self.album_container.winfo_children():
            widget.destroy()

        # 필터링된 앨범 표시
        playlists = self.db_manager.get_all_playlists()
        for playlist_id, title, url in playlists:
            if search_term in title.lower():
                self.create_album_card(playlist_id, title, url)

    def edit_album(self, playlist_id):
        """앨범 정보 수정"""
        try:
            # 현재 앨범 정보 가져오기
            playlist = self.db_manager.get_playlist_by_id(playlist_id)
            if not playlist:
                raise Exception("앨범을 찾을 수 없습니다.")

            # 새 제목 입력 받기
            new_title = ctk.CTkInputDialog(
                text="새 앨범 제목을 입력하세요:",
                title="앨범 수정"
            ).get_input()

            if new_title:
                self.db_manager.update_playlist_title(playlist_id, new_title)
                messagebox.showinfo("성공", "앨범 정보가 수정되었습니다.")
                self.load_albums()  # 목록 새로고침

        except Exception as e:
            messagebox.showerror("Error", f"앨범 수정 중 오류 발생: {e}")

    def delete_album(self, playlist_id):
        """앨범 삭제"""
        if messagebox.askyesno("확인", "정말 이 앨범을 삭제하시겠습니까?"):
            try:
                self.db_manager.delete_playlist(playlist_id)
                messagebox.showinfo("성공", "앨범이 삭제되었습니다.")

                # 기존 앨범 카드들 제거
                for widget in self.album_container.winfo_children():
                    widget.destroy()

                # 앨범 목록 다시 로드
                self.load_albums()

                # 컨테이너 업데이트 강제 실행
                self.album_container.update_idletasks()
                self.update_idletasks()

            except Exception as e:
                messagebox.showerror("Error", f"앨범 삭제 중 오류 발생: {e}")

    def view_playlist(self, playlist_id):
        """플레이리스트 뷰어로 전환"""
        try:
            # 메인 앱의 current_playlist_id 업데이트
            self.main_app.set_current_playlist(playlist_id)

            # Playlist 탭으로 전환하고 해당 플레이리스트 표시
            self.main_app.load_and_show_playlist(playlist_id)

        except Exception as e:
            messagebox.showerror("Error", f"플레이리스트 전환 중 오류 발생: {e}")