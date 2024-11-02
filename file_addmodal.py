import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import customtkinter as ctk
import os


class FileAddModal(ctk.CTkToplevel):
    def __init__(self, parent, on_save_callback):
        super().__init__(parent)
        self.on_save_callback = on_save_callback
        self.added_files = []

        # 모달 창 설정
        self.title("Add New Group and Files")
        self.geometry("400x500")
        self.configure(fg_color="#1E1B2E")
        self.resizable(False, False)

        # 그룹명 입력
        ctk.CTkLabel(self, text="그룹명", font=("Helvetica", 14)).pack(pady=(20, 10))
        self.group_name_entry = ctk.CTkEntry(self, placeholder_text="Enter group name...", fg_color="#2D2640")
        self.group_name_entry.pack(padx=20, fill="x")

        # 파일 추가 버튼을 "추가된 파일" 타이틀 대신 상단에 배치
        self.file_add_button = ctk.CTkButton(self, text="파일 추가", command=self.add_files)
        self.file_add_button.pack(pady=(20, 10))

        # 추가된 파일 리스트 프레임
        self.file_list_frame = ctk.CTkScrollableFrame(self, fg_color="#2D2640", height=200)
        self.file_list_frame.pack(padx=20, fill="both", expand=True)

        # 저장 버튼
        self.save_button = ctk.CTkButton(self, text="저장", command=self.save_group)
        self.save_button.pack(pady=20)

        self.update_file_list()

    def add_files(self):
        """파일 대화창을 열어 파일을 선택하고 추가된 파일 목록에 반영합니다."""
        files = filedialog.askopenfilenames(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg"), ("All Files", "*.*")])
        for file in files:
            if file not in self.added_files:
                self.added_files.append(file)
        self.update_file_list()

    def update_file_list(self):
        """추가된 파일 목록을 UI에 업데이트합니다."""
        # 기존 항목 삭제
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        # 새로 추가된 파일 목록 표시
        for file in self.added_files:
            file_name = os.path.basename(file)
            ctk.CTkLabel(self.file_list_frame, text=file_name, fg_color="#2D2640", font=("Helvetica", 12)).pack(
                anchor="w", padx=10, pady=5)

    def save_group(self):
        """그룹명과 추가된 파일을 저장합니다."""
        group_name = self.group_name_entry.get().strip()
        if not group_name:
            messagebox.showerror("Error", "그룹명을 입력하세요.")
            return

        if not self.added_files:
            messagebox.showerror("Error", "추가된 파일이 없습니다.")
            return

        # 콜백 함수를 호출하여 부모 창에 그룹명과 파일 목록을 전달
        self.on_save_callback(group_name, self.added_files)
        self.destroy()  # 모달 창 닫기
