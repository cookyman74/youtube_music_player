from tkinter import Frame, Listbox, Scrollbar, VERTICAL
from controllers.audiobox_controller import AudioboxController


class Audiobox(Frame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = AudioboxController(self)

        # GUI 구성 요소 추가 (리스트박스, 스크롤바 등)
        self.listbox = Listbox(self, selectmode='extended', width=40, height=15)
        scrollbar = Scrollbar(self, orient=VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)

        self.listbox.pack(side="left")
        scrollbar.pack(side="right", fill="y")

        # 이벤트 바인딩
        self.listbox.bind('<<ListboxSelect>>', self.controller.on_select)

        # Pack layout 설정
        self.pack()