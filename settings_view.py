import customtkinter as ctk
from tkinter import filedialog, messagebox
import os


class SettingsView(ctk.CTkToplevel):
    """설정 화면을 위한 설정 뷰"""

    def __init__(self, master, config, on_reset_callback):
        super().__init__(master)
        self.config = config
        self.on_reset_callback = on_reset_callback

        self.title("Settings")
        self.geometry("400x300")
        self.configure(fg_color="#1E1B2E")

        # 음악 다운로드 위치 설정
        self.create_download_directory_setting()

        # 유튜브 계정 설정
        self.create_youtube_account_setting()

        # 다운로드 정보 표시 (앨범수 및 트랙수)
        self.create_download_info_setting()

        # 전체 초기화 버튼
        self.create_reset_button()

    def create_download_directory_setting(self):
        """음악 다운로드 위치 설정 섹션 생성"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            frame,
            text="Set Playlist Directory",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w")

        self.download_directory_label = ctk.CTkLabel(
            frame,
            text=self.config.get("download_directory", "Not Set"),
            font=("Helvetica", 12),
            text_color="gray"
        )
        self.download_directory_label.pack(anchor="w", padx=10, pady=5)

        ctk.CTkButton(
            frame,
            text="Browse",
            command=self.set_download_directory
        ).pack(anchor="e", padx=10)

    def set_download_directory(self):
        """음악 다운로드 위치 설정"""
        directory = filedialog.askdirectory()
        if directory:
            self.config["download_directory"] = directory
            self.download_directory_label.configure(text=directory)
            # 설정을 저장하거나 필요한 추가 작업을 수행할 수 있습니다.

    def create_youtube_account_setting(self):
        """유튜브 계정 설정 섹션 생성"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            frame,
            text="YouTube Account Settings",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w")

        self.youtube_account_label = ctk.CTkLabel(
            frame,
            text="Not Connected",
            font=("Helvetica", 12),
            text_color="gray"
        )
        self.youtube_account_label.pack(anchor="w", padx=10, pady=5)

        ctk.CTkButton(
            frame,
            text="Connect",
            command=self.connect_youtube_account
        ).pack(anchor="e", padx=10)

    def connect_youtube_account(self):
        """유튜브 계정 설정"""
        # 여기에서 YouTube API와 연동하여 OAuth 인증 절차를 진행할 수 있습니다.
        # 예를 들어, 인증 성공 시 self.youtube_account_label을 "Connected"로 변경합니다.
        self.youtube_account_label.configure(text="Connected")

    def create_download_info_setting(self):
        """다운로드 정보 표시 섹션 생성"""
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            frame,
            text="Download Information",
            font=("Helvetica", 14, "bold")
        ).pack(anchor="w")

        # 다운로드 받은 앨범 수 및 트랙 수를 표시
        self.album_count_label = ctk.CTkLabel(
            frame,
            text=f"Albums downloaded: {self.get_album_count()}",
            font=("Helvetica", 12),
            text_color="gray"
        )
        self.album_count_label.pack(anchor="w", padx=10, pady=5)

        self.track_count_label = ctk.CTkLabel(
            frame,
            text=f"Tracks downloaded: {self.get_track_count()}",
            font=("Helvetica", 12),
            text_color="gray"
        )
        self.track_count_label.pack(anchor="w", padx=10)

    def get_album_count(self):
        """앨범 수 가져오기 (예: 다운로드 디렉토리의 하위 폴더 수)"""
        download_dir = self.config.get("download_directory")
        if download_dir and os.path.isdir(download_dir):
            return len([f for f in os.listdir(download_dir) if os.path.isdir(os.path.join(download_dir, f))])
        return 0

    def get_track_count(self):
        """트랙 수 가져오기 (예: 다운로드 디렉토리 내의 파일 수)"""
        download_dir = self.config.get("download_directory")
        if download_dir and os.path.isdir(download_dir):
            return len([f for f in os.listdir(download_dir) if os.path.isfile(os.path.join(download_dir, f))])
        return 0

    def create_reset_button(self):
        """전체 초기화 버튼 생성"""
        reset_button = ctk.CTkButton(
            self,
            text="Reset All Settings",
            fg_color="#FF4B8C",
            hover_color="#FF6A9F",
            command=self.reset_all_settings
        )
        reset_button.pack(pady=20)

    def reset_all_settings(self):
        """전체 설정 초기화 기능"""
        if messagebox.askyesno("Reset All", "Are you sure you want to reset all settings?"):
            self.config.clear()
            self.download_directory_label.configure(text="Not Set")
            self.youtube_account_label.configure(text="Not Connected")
            self.album_count_label.configure(text="Albums downloaded: 0")
            self.track_count_label.configure(text="Tracks downloaded: 0")
            if self.on_reset_callback:
                self.on_reset_callback()  # 메인 앱에 초기화 콜백 호출
