import customtkinter as ctk
from tkinter import messagebox

class PlaylistViewer:
    def __init__(self, parent, db_manager):
        self.parent = parent  # ModernPurplePlayer 클래스의 인스턴스 참조
        self.db_manager = db_manager
        self.playlist_container = None  # 트랙을 표시할 UI 컨테이너

    def create_playlist_view(self, container):
        """Create playlist view in the provided container."""
        self.playlist_container = ctk.CTkScrollableFrame(container, fg_color="#1E1B2E")
        self.playlist_container.pack(fill="both", expand=True)
        self.update_playlist_ui()

    def update_playlist_ui(self, playlist_id):
        """특정 앨범의 트랙 목록을 DB에서 가져와 UI를 업데이트"""
        for widget in self.playlist_container.winfo_children():
            widget.destroy()

        tracks = self.db_manager.get_tracks_by_playlist(playlist_id)
        for track_id, title, artist, file_path in tracks:
            track_frame = ctk.CTkFrame(self.playlist_container, fg_color="#2D2640", corner_radius=10)
            track_frame.pack(fill="x", pady=5, padx=10)

            title_entry = ctk.CTkEntry(track_frame, font=("Helvetica", 14, "bold"))
            title_entry.insert(0, title)
            title_entry.pack(side="left", padx=5)

            edit_button = ctk.CTkButton(
                track_frame, text="Edit",
                command=lambda e=title_entry, tid=track_id: self.edit_track_title(e, tid)
            )
            edit_button.pack(side="left", padx=5)

            delete_button = ctk.CTkButton(
                track_frame, text="Delete", fg_color="red",
                command=lambda tid=track_id: self.delete_track(tid)
            )
            delete_button.pack(side="left", padx=5)

    def edit_track_title(self, title_entry, track_id):
        """트랙 제목을 DB에 저장"""
        new_title = title_entry.get()
        self.db_manager.update_track_title(track_id, new_title)
        self.update_playlist_ui()  # UI 업데이트

    def delete_track(self, track_id):
        """트랙 삭제 및 UI 업데이트"""
        if messagebox.askyesno("Delete Track", "Are you sure you want to delete this track?"):
            self.db_manager.delete_track(track_id)
            self.update_playlist_ui()  # UI 업데이트
