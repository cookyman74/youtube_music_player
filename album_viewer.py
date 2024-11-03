import customtkinter as ctk
from tkinter import messagebox

class AlbumViewer:
    def __init__(self, parent, db_manager):
        self.parent = parent  # ModernPurplePlayer 클래스의 인스턴스 참조
        self.db_manager = db_manager
        self.album_grid_frame = None  # 앨범을 표시할 UI 컨테이너

    def create_album_view(self, container):
        """Create album view in the provided container."""
        self.album_grid_frame = ctk.CTkFrame(container, fg_color="#1E1B2E")
        self.album_grid_frame.pack(fill="both", expand=True)
        self.update_album_ui()

    def update_album_ui(self):
        """데이터베이스에서 앨범 목록을 가져와 UI를 업데이트"""
        for widget in self.album_grid_frame.winfo_children():
            widget.destroy()

        playlists = self.db_manager.get_all_playlists()
        for playlist_id, title, url in playlists:
            playlist_frame = ctk.CTkFrame(self.album_grid_frame, fg_color="#2D2640", corner_radius=10)
            playlist_frame.pack(fill="x", pady=5, padx=10)

            # 앨범 제목 수정 가능한 Entry
            title_entry = ctk.CTkEntry(playlist_frame, font=("Helvetica", 14, "bold"))
            title_entry.insert(0, title)
            title_entry.pack(side="left", padx=5)

            # Edit 버튼
            edit_button = ctk.CTkButton(
                playlist_frame, text="Edit",
                command=lambda e=title_entry, pid=playlist_id: self.edit_album_title(e, pid)
            )
            edit_button.pack(side="left", padx=5)

            # Delete 버튼
            delete_button = ctk.CTkButton(
                playlist_frame, text="Delete", fg_color="red",
                command=lambda pid=playlist_id: self.delete_album(pid)
            )
            delete_button.pack(side="left", padx=5)

    def edit_album_title(self, title_entry, playlist_id):
        """앨범 제목을 DB에 저장"""
        new_title = title_entry.get()
        self.db_manager.update_playlist_title(playlist_id, new_title)
        self.update_album_ui()  # UI 업데이트

    def delete_album(self, playlist_id):
        """앨범 삭제 및 UI 업데이트"""
        if messagebox.askyesno("Delete Album", "Are you sure you want to delete this album?"):
            self.db_manager.delete_playlist(playlist_id)
            self.update_album_ui()  # UI 업데이트
