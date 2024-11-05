# settings_view.py

import customtkinter as ctk
import logging
from tkinter import messagebox  # 최상단에 추가


class SettingsView(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, reset_callback, album_count, track_count):
        super().__init__(parent)

        # Store parameters
        self.parent = parent
        self.db_manager = db_manager
        self.reset_callback = reset_callback

        # Logger 설정
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Window setup
        self.title("Settings")
        self.geometry("400x530")
        self.configure(fg_color=parent.purple_dark)

        # Load current settings
        self.current_settings = self._load_current_settings()

        # Create main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create sections
        self.create_audio_settings()  # 오디오 설정 섹션 추가
        self.create_directory_settings() # 디렉토리 설정.
        self.create_youtube_account_section()  # YouTube 계정 섹션 추가
        self.create_statistics_section(album_count, track_count)
        self.create_reset_button()

    def _load_current_settings(self) -> dict:
        """현재 설정값 로드"""
        try:
            return {
                'youtube_api_key': self.db_manager.get_setting('youtube_api_key') or '',
                'download_directory': self.db_manager.get_setting('download_directory') or 'downloads',
                'theme_mode': self.db_manager.get_setting('theme_mode') or 'dark',
                'default_volume': float(self.db_manager.get_setting('default_volume') or 0.5),
                'preferred_codec': self.db_manager.get_setting('preferred_codec') or 'mp3',  # 추가
                'preferred_quality': self.db_manager.get_setting('preferred_quality') or '192'  # 추가
            }
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            # 기본값 반환
            return {
                'youtube_api_key': '',
                'download_directory': 'downloads',
                'theme_mode': 'dark',
                'default_volume': 0.5,
                'preferred_codec': 'mp3',
                'preferred_quality': '192'
            }

    def create_youtube_account_section(self):
        """YouTube 계정 설정 섹션 생성"""
        youtube_frame = ctk.CTkFrame(self.main_frame)
        youtube_frame.pack(fill="x", pady=(0, 20))

        # Title frame with "YouTube Account" label and "Save API Key" button
        title_frame = ctk.CTkFrame(youtube_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=5)

        # Title label
        ctk.CTkLabel(
            title_frame,
            text="유튜브 연동 설정",
            font=("Helvetica", 16, "bold")
        ).pack(side="left")

        # Save API Key button next to the title
        ctk.CTkButton(
            title_frame,
            text="API 저장",
            command=self.save_api_key
        ).pack(side="right")

        # API Key input frame
        api_key_frame = ctk.CTkFrame(youtube_frame, fg_color="transparent")
        api_key_frame.pack(fill="x", padx=10, pady=5)

        # API Key label
        ctk.CTkLabel(
            api_key_frame,
            text="API Key:",
            font=("Helvetica", 12, "bold")
        ).pack(side="left", padx=(0, 5))

        # API Key entry field (masked)
        self.api_key_entry = ctk.CTkEntry(
            api_key_frame,
            placeholder_text="Enter YouTube API Key",
            show="*",  # 마스킹 처리
            width=200
        )
        self.api_key_entry.pack(side="left", expand=True)

        # Show/Hide API Key button
        self.show_key_button = ctk.CTkButton(
            api_key_frame,
            text="👁",
            width=30,
            command=self.toggle_api_key_visibility
        )
        self.show_key_button.pack(side="right", padx=(5, 0))

        # Load current API key
        current_api_key = self.current_settings.get('youtube_api_key')
        if current_api_key:
            self.api_key_entry.insert(0, current_api_key)

        # Help text with [바로가기] link button
        help_text = """
    YouTube API 키를 얻으려면:
        1. Google Cloud Console에 접속하세요.
        2. 새 프로젝트를 만드세요.
        3. YouTube Data API v3을 활성화하세요.
        4. 인증 정보를 생성하세요 (API 키)
    """

        help_label = ctk.CTkLabel(
            youtube_frame,
            text=help_text,
            font=("Helvetica", 12),
            justify="left",
            text_color="gray",
            wraplength=350
        )
        help_label.pack(anchor="w", padx=10, pady=(5, 0))

        # Add "Get API Key" button that opens Google Cloud Console
        # ctk.CTkButton(
        #     youtube_frame,
        #     text="개발자 콘솔 바로가기",
        #     command=self.open_google_console
        # ).pack(anchor="w", padx=10, pady=5)

    def create_statistics_section(self, album_count, track_count):
        """통계 섹션 생성"""
        stats_frame = ctk.CTkFrame(self.main_frame)
        stats_frame.pack(fill="x", pady=(0, 20))

        # Title
        ctk.CTkLabel(
            stats_frame,
            text="Statistics",
            font=("Helvetica", 16, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        # Album count
        ctk.CTkLabel(
            stats_frame,
            text=f"Albums: {album_count}",
            font=("Helvetica", 12)
        ).pack(anchor="w", padx=10, pady=2)

        # Track count
        ctk.CTkLabel(
            stats_frame,
            text=f"Tracks: {track_count}",
            font=("Helvetica", 12)
        ).pack(anchor="w", padx=10, pady=2)

    def toggle_api_key_visibility(self):
        """API Key 표시/숨김 토글"""
        current_show = self.api_key_entry.cget("show")
        if current_show == "*":
            self.api_key_entry.configure(show="")
            self.show_key_button.configure(text="🔒")
        else:
            self.api_key_entry.configure(show="*")
            self.show_key_button.configure(text="👁")

    def save_api_key(self):
        """API Key 저장"""
        api_key = self.api_key_entry.get()
        if api_key:
            try:
                self.db_manager.save_youtube_api_key(api_key)
                self.show_success_message("API Key saved successfully")
            except Exception as e:
                self.show_error_message(f"Failed to save API Key: {e}")
        else:
            self.show_error_message("Please enter an API Key")

    def open_google_console(self):
        """Google Cloud Console 열기"""
        import webbrowser
        webbrowser.open("https://console.cloud.google.com/apis/dashboard")

    def create_directory_settings(self):
        """디렉토리 설정 섹션 생성"""
        dir_frame = ctk.CTkFrame(self.main_frame)
        dir_frame.pack(fill="x", pady=(0, 20))

        # Title frame with "Directory Settings" label and "Change Directory" button
        title_frame = ctk.CTkFrame(dir_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=5)

        # Title label
        ctk.CTkLabel(
            title_frame,
            text="다운로드 디렉토리 설정",
            font=("Helvetica", 16, "bold")
        ).pack(side="left")

        # Change Directory button next to the title
        ctk.CTkButton(
            title_frame,
            text="설정변경",
            command=self.change_download_directory
        ).pack(side="right")

        # Get current download directory from the database
        current_directory = self.current_settings.get("download_directory")

        # Download directory label
        self.download_dir_label = ctk.CTkLabel(
            dir_frame,
            text=f"다운로드 경로: {current_directory}",
            font=("Helvetica", 12),
            text_color="gray"
        )
        self.download_dir_label.pack(anchor="w", padx=10, pady=2)

    def create_audio_settings(self):
        """오디오 설정 섹션 생성"""
        audio_frame = ctk.CTkFrame(self.main_frame)
        audio_frame.pack(fill="x", pady=(0, 20))

        # Title
        ctk.CTkLabel(
            audio_frame,
            text="오디오 설정",
            font=("Helvetica", 16, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        # Codec Selection
        codec_frame = ctk.CTkFrame(audio_frame, fg_color="transparent")
        codec_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            codec_frame,
            text="저장할 코덱:",
            font=("Helvetica", 12)
        ).pack(side="left", padx=(0, 10))

        # Codec dropdown
        codec_options = ['mp3', 'aac', 'm4a', 'wav', 'flac']
        self.codec_var = ctk.StringVar(value=self.current_settings.get('preferred_codec', 'mp3'))
        codec_dropdown = ctk.CTkOptionMenu(
            codec_frame,
            values=codec_options,
            variable=self.codec_var,
            command=self._on_codec_change
        )
        codec_dropdown.pack(side="left", expand=True)

        # Quality Selection
        quality_frame = ctk.CTkFrame(audio_frame, fg_color="transparent")
        quality_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            quality_frame,
            text="오디오 품질:",
            font=("Helvetica", 12)
        ).pack(side="left", padx=(0, 10))

        # Quality dropdown
        quality_options = ['64', '128', '192', '256', '320']  # kbps
        self.quality_var = ctk.StringVar(value=self.current_settings.get('preferred_quality', '192'))
        quality_dropdown = ctk.CTkOptionMenu(
            quality_frame,
            values=quality_options,
            variable=self.quality_var,
            command=self._on_quality_change
        )
        quality_dropdown.pack(side="left", expand=True)

        # Quality explanation
        quality_info = """Audio Quality Guide:
        64 kbps  - Basic quality, smallest file size
        128 kbps - Standard quality
        192 kbps - High quality (recommended)
        256 kbps - Very high quality
        320 kbps - Maximum quality, largest file size"""

        ctk.CTkLabel(
            audio_frame,
            text=quality_info,
            font=("Helvetica", 10),
            justify="left",
            text_color="gray"
        ).pack(anchor="w", padx=10, pady=5)

    def _on_codec_change(self, codec: str):
        """코덱 변경 처리"""
        try:
            self.db_manager.save_setting('preferred_codec', codec)
            self.show_success_message(f"Audio codec changed to {codec}")
        except Exception as e:
            self.logger.error(f"Error changing codec: {e}")
            self.show_error_message("Failed to update audio codec")

    def _on_quality_change(self, quality: str):
        """음질 변경 처리"""
        try:
            self.db_manager.save_setting('preferred_quality', quality)
            self.show_success_message(f"Audio quality changed to {quality}kbps")
        except Exception as e:
            self.logger.error(f"Error changing quality: {e}")
            self.show_error_message("Failed to update audio quality")

    def create_reset_button(self):
        """리셋 버튼 생성"""
        reset_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        reset_frame.pack(fill="x", side="bottom", pady=20)

        ctk.CTkButton(
            reset_frame,
            text="Reset Settings",
            fg_color="#FF4B4B",  # 빨간색 계열
            hover_color="#FF6B6B",
            command=self.confirm_reset
        ).pack(side="bottom", fill="x")

    def change_download_directory(self):
        """다운로드 디렉토리 변경"""
        directory = ctk.filedialog.askdirectory()
        if directory:
            self.db_manager.update_download_directory(directory)
            self.download_dir_label.configure(text=f"Download Directory: {directory}")

    def confirm_reset(self):
        """설정 초기화 확인"""
        dialog = ctk.CTkInputDialog(
            text="Type 'RESET' to confirm settings reset:",
            title="Confirm Reset"
        )
        result = dialog.get_input()

        if result == "RESET":
            self.reset_settings()

    def reset_settings(self):
        """설정 초기화"""
        try:
            # Reset database
            self.db_manager.reset_database()

            # Reset download directory
            self.download_dir_label.configure(text="Download Directory: Not Set")

            # Call parent's reset callback
            if self.reset_callback:
                self.reset_callback()

            # Show success message
            self.show_success_message("Settings have been reset successfully")

        except Exception as e:
            self.show_error_message(f"Error resetting settings: {e}")

    def show_success_message(self, message):
        """성공 메시지 표시"""
        messagebox.showinfo("Success", message)

    def show_error_message(self, message):
        """에러 메시지 표시"""
        messagebox.showerror("Error", message)

