class AudioboxController:
    def __init__(self, view):
        self.view = view

    def on_select(self, event):
        # 선택된 항목에 대한 로직 처리
        selected_index = self.view.listbox.curselection()
        print(f"선택된 항목: {selected_index}")