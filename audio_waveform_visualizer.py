import numpy as np
import wave
import audioop
from scipy.io import wavfile
import pygame
from pydub import AudioSegment
import io


class AudioWaveformVisualizer:
    def __init__(self, canvas, color, bg_color):
        self.canvas = canvas
        self.color = color
        self.bg_color = bg_color
        self.chunk_size = 1024
        self.current_frame = 0
        self.waveform_points = []

    def load_audio(self, audio_path):
        """Load and process audio file for visualization"""
        try:
            # Convert audio to WAV format if needed
            if not audio_path.endswith('.wav'):
                audio = AudioSegment.from_file(audio_path)
                audio = audio.set_channels(1)  # Convert to mono
                wav_io = io.BytesIO()
                audio.export(wav_io, format='wav')
                wav_io.seek(0)
                audio_file = wave.open(wav_io)
            else:
                audio_file = wave.open(audio_path, 'rb')

            # Get audio properties
            self.channels = audio_file.getnchannels()
            self.sample_width = audio_file.getsampwidth()
            self.sample_rate = audio_file.getframerate()
            self.num_frames = audio_file.getnframes()

            # Read all frames and calculate RMS values
            frames = audio_file.readframes(self.num_frames)
            self.waveform_points = self._calculate_waveform_points(frames)

            audio_file.close()
            return True

        except Exception as e:
            print(f"Error loading audio: {e}")
            return False

    def _calculate_waveform_points(self, frames):
        """Calculate RMS values for visualization"""
        points = []
        for i in range(0, len(frames), self.chunk_size):
            chunk = frames[i:i + self.chunk_size]
            rms = audioop.rms(chunk, self.sample_width)
            # Normalize RMS value
            normalized_rms = min(1.0, rms / 32768)
            points.append(normalized_rms)
        return points

    def draw_waveform(self, start_frame=0, width=None, height=None):
        """Draw waveform on canvas"""
        if not self.waveform_points:
            return

        # Clear canvas
        self.canvas.delete("all")

        # Get canvas dimensions
        width = width or self.canvas.winfo_width()
        height = height or self.canvas.winfo_height()
        center_y = height / 2

        # Calculate how many points to display
        points_to_display = min(len(self.waveform_points), width // 3)
        start_idx = int(start_frame / self.num_frames * len(self.waveform_points))

        # Draw waveform bars
        bar_width = 2
        gap_width = 1
        for i in range(points_to_display):
            if start_idx + i >= len(self.waveform_points):
                break

            amplitude = self.waveform_points[start_idx + i]
            bar_height = amplitude * (height * 0.8)  # Use 80% of canvas height

            x = i * (bar_width + gap_width)

            # Draw mirrored bars
            self.canvas.create_rectangle(
                x, center_y - bar_height / 2,
                   x + bar_width, center_y + bar_height / 2,
                fill=self.color,
                width=0
            )

    def update_position(self, current_time, total_time):
        """Update waveform position based on current playback time"""
        if total_time > 0:
            progress = current_time / total_time
            start_frame = int(progress * self.num_frames)
            self.draw_waveform(start_frame)


class RealTimeWaveformUpdater:
    def __init__(self, visualizer, player):
        self.visualizer = visualizer
        self.player = player
        self.is_running = False

    def start_update(self):
        """Start real-time waveform updates"""
        self.is_running = True
        self._update_loop()

    def stop_update(self):
        """Stop real-time updates"""
        self.is_running = False

    def _update_loop(self):
        """Update waveform visualization in real-time"""
        if not self.is_running:
            return

        if self.player.get_busy():
            current_time = self.player.get_pos() / 1000  # Convert to seconds
            total_time = self.visualizer.num_frames / self.visualizer.sample_rate
            self.visualizer.update_position(current_time, total_time)

        # Schedule next update
        self.player.after(50, self._update_loop)  # Update every 50ms