# settings_view.py

import customtkinter as ctk


class SettingsView(ctk.CTkToplevel):
    def __init__(self, parent, db_manager, reset_callback, album_count, track_count):
        super().__init__(parent)

        # Store parameters
        self.parent = parent
        self.db_manager = db_manager
        self.reset_callback = reset_callback

        # Window setup
        self.title("Settings")
        self.geometry("400x500")
        self.configure(fg_color=parent.purple_dark)

        # Create main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create sections
        self.create_statistics_section(album_count, track_count)
        self.create_youtube_account_section()  # YouTube 계정 섹션 추가
        self.create_directory_settings()
        self.create_reset_button()

    def create_youtube_account_section(self):
        """YouTube 계정 설정 섹션 생성"""
        youtube_frame = ctk.CTkFrame(self.main_frame)
        youtube_frame.pack(fill="x", pady=(0, 20))

        # Title
        ctk.CTkLabel(
            youtube_frame,
            text="YouTube Account",
            font=("Helvetica", 16, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        # API Key input
        api_key_frame = ctk.CTkFrame(youtube_frame, fg_color="transparent")
        api_key_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            api_key_frame,
            text="API Key:",
            font=("Helvetica", 12)
        ).pack(side="left", padx=(0, 10))

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

        # Save API Key button
        ctk.CTkButton(
            youtube_frame,
            text="Save API Key",
            command=self.save_api_key
        ).pack(anchor="w", padx=10, pady=5)

        # Load current API key
        current_api_key = self.db_manager.get_youtube_api_key()
        if current_api_key:
            self.api_key_entry.insert(0, current_api_key)

        # Help text
        help_text = """To get a YouTube API key:
1. Go to Google Cloud Console
2. Create a new project
3. Enable YouTube Data API v3
4. Create credentials (API key)"""

        help_label = ctk.CTkLabel(
            youtube_frame,
            text=help_text,
            font=("Helvetica", 10),
            justify="left",
            wraplength=350
        )
        help_label.pack(anchor="w", padx=10, pady=5)

        # Add "Get API Key" button that opens Google Cloud Console
        ctk.CTkButton(
            youtube_frame,
            text="Get API Key",
            command=self.open_google_console
        ).pack(anchor="w", padx=10, pady=5)

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

        # Title
        ctk.CTkLabel(
            dir_frame,
            text="Directory Settings",
            font=("Helvetica", 16, "bold")
        ).pack(anchor="w", padx=10, pady=5)

        # Download directory
        self.download_dir_label = ctk.CTkLabel(
            dir_frame,
            text="Download Directory:",
            font=("Helvetica", 12)
        )
        self.download_dir_label.pack(anchor="w", padx=10, pady=2)

        # Change directory button
        ctk.CTkButton(
            dir_frame,
            text="Change Directory",
            command=self.change_download_directory
        ).pack(anchor="w", padx=10, pady=5)

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
        ctk.messagebox.showinfo("Success", message)

    def show_error_message(self, message):
        """에러 메시지 표시"""
        ctk.messagebox.showerror("Error", message)