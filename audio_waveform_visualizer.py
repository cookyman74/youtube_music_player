import numpy as np
import wave
import audioop
from scipy.io import wavfile
import pygame
from pydub import AudioSegment
import io


class AudioWaveformVisualizer:
    def __init__(self, canvas, waveform_color, background_color):
        self.canvas = canvas
        self.waveform_color = waveform_color
        self.background_color = background_color
        self.wave_points = []
        self.wave_height = self.canvas.winfo_height()

    def draw_waveform(self, points):
        """Draw waveform on canvas"""
        self.canvas.delete("all")
        if not points:
            return

        # 캔버스 크기 가져오기
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # 중심선 그리기
        center_y = height // 2

        # 파형 그리기
        for i in range(len(points) - 1):
            x1 = i * (width / len(points))
            x2 = (i + 1) * (width / len(points))
            y1 = center_y + (points[i] * height / 2)
            y2 = center_y + (points[i + 1] * height / 2)

            self.canvas.create_line(x1, y1, x2, y2, fill=self.waveform_color)

    def generate_wave_points(self, num_points=50):
        """Generate random wave points for visualization"""
        import random
        import math

        points = []
        for i in range(num_points):
            # 사인파와 랜덤 노이즈를 조합
            wave = math.sin(i * 0.2) * 0.3
            noise = random.uniform(-0.1, 0.1)
            point = wave + noise
            points.append(point)

        return points

    def update_waveform(self):
        """Update waveform visualization"""
        try:
            new_points = self.generate_wave_points()
            self.draw_waveform(new_points)
        except Exception as e:
            print(f"Error updating waveform: {e}")

class RealTimeWaveformUpdater:
    def __init__(self, visualizer, player):
        self.visualizer = visualizer
        self.player = player
        self._is_running = False
        self._after_id = None

    def start_update(self):
        """Start the update loop"""
        self._is_running = True
        self._update_loop()

    def stop_update(self):
        """Stop the update loop"""
        self._is_running = False
        if self._after_id:
            self.visualizer.canvas.after_cancel(self._after_id)
            self._after_id = None

    def _update_loop(self):
        """Update loop for the waveform visualization"""
        if self._is_running and self.player.is_playing and not self.player.is_seeking:
            try:
                self.visualizer.update_waveform()
            except Exception as e:
                print(f"Waveform update error: {e}")

        # 다음 업데이트 예약 (더 부드러운 애니메이션을 위해 간격 조정)
        if self._is_running:
            self._after_id = self.visualizer.canvas.after(100, self._update_loop)