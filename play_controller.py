class PlayController:
    def __init__(self, db_manager, view):
        self.db_manager = db_manager
        self.view = view
        self.playlist = []
        self.current_index = -1
        self.is_playing = False
        self.current_position = 0.0
        self.initialize_audio_engine()

    # 새로 추가할 메서드들
    def update_progress(self, value):
        """프로그레스바 값 업데이트 및 재생 위치 변경"""
        if self.current_index >= 0:
            total_length = self.get_audio_length()
            new_position = total_length * value
            self.seek_to_position(new_position)
            self.view.update_progress_bar(value)

    def seek_to_position(self, position):
        """특정 위치로 재생 위치 변경"""
        if self.current_index >= 0:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.playlist[self.current_index]['path'])
            pygame.mixer.music.play(start=int(position))
            self.current_position = position

    def get_audio_length(self):
        """현재 재생 중인 오디오 파일의 길이 반환"""
        if self.current_index >= 0:
            try:
                audio = File(self.playlist[self.current_index]['path'])
                return float(audio.info.length)
            except Exception as e:
                print(f"Error getting audio length: {e}")
        return 0.0

    def update_player_state(self):
        """주기적으로 플레이어 상태 업데이트"""
        if self.is_playing:
            current_pos = pygame.mixer.music.get_pos() / 1000
            total_length = self.get_audio_length()
            progress = current_pos / total_length if total_length > 0 else 0
            self.view.update_progress_bar(progress)