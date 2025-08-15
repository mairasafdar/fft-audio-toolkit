import sys
import os
import numpy as np
from scipy.io import wavfile
import tempfile
import time

# Import all the necessary components from PyQt6
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QSlider, QLabel, QFileDialog, QGraphicsView, QGraphicsScene,
                             QGraphicsPathItem, QPushButton, QStackedWidget, QFrame)
from PyQt6.QtGui import QPen, QColor, QPainterPath, QFont
from PyQt6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, QRect, QSize, QTimer)

# We need to import pygame here to initialize it
import pygame
import audio_utils

# --- Stylesheet ---
MODERN_STYLESHEET = """
    /* Main Window Styling */
    QMainWindow, QWidget {
        background-color: #1e1e1e; /* Off-black for a professional look */
        color: #f0f0f0; /* Off-white for text */
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
    }

    /* Title Labels */
    QLabel#TitleLabel {
        font-size: 28px;
        font-weight: bold;
        color: #f0f0f0;
    }

    /* Standard Labels */
    QLabel {
        font-size: 16px;
    }

    /* Button Styling */
    QPushButton {
        background-color: #333333;
        border: 1px solid #555555;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #444444;
        border: 1px solid #777777;
    }
    QPushButton#AccentButton {
        background-color: #ff007f; /* Vibrant Magenta/Pink */
        color: white;
    }
    QPushButton#AccentButton:hover {
        background-color: #cc0066;
    }

    /* Slider Styling */
    QSlider::groove:horizontal {
        border: 1px solid #333333;
        height: 4px;
        background: #444444;
        margin: 2px 0;
        border-radius: 2px;
    }
    QSlider::handle:horizontal {
        background: #ff007f; /* Vibrant Magenta/Pink */
        border: 2px solid #1e1e1e;
        width: 18px;
        margin: -8px 0; 
        border-radius: 9px;
    }

    /* Waveform Viewer Styling */
    QGraphicsView {
        border-radius: 8px;
        background-color: #2b2b2b;
        border: 1px solid #444444;
    }
"""


class AudioApp(QMainWindow):
    def __init__(self):
        super().__init__()

        pygame.init()
        pygame.mixer.init()

        self.setWindowTitle("Audio Toolkit")
        self.setGeometry(100, 100, 1024, 700)
        self.setStyleSheet(MODERN_STYLESHEET)

        # --- App State ---
        self.filepath = None
        self.original_audio_data = None
        self.eq_audio_data = None
        self.sample_rate = 0
        self.original_filesize_kb = 0
        self.song_length_ms = 0
        self.temp_preview_file = None

        # --- Playback State ---
        self.is_playing = False
        self.is_paused = False
        self.playback_pos_ms = 0
        self.playback_start_offset_ms = 0
        self.settings_changed_since_play = False

        # --- Playback Timer ---
        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(50)
        self.playback_timer.timeout.connect(self.update_progress)

        # --- UI Setup ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        self.create_welcome_screen()

    def create_welcome_screen(self):
        welcome_page = QWidget()
        layout = QVBoxLayout(welcome_page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("FFT Audio Toolkit")
        title.setObjectName("TitleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("A modern audio editor for .wav files using Fast Fourier Transform")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        load_button = QPushButton("Load .wav File")
        load_button.setObjectName("AccentButton")
        load_button.setFixedSize(200, 50)
        load_button.clicked.connect(self.open_file_dialog)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(30)
        layout.addWidget(load_button, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        self.stacked_widget.addWidget(welcome_page)

    def open_file_dialog(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Open WAV File", "", "WAV Files (*.wav)")
        if filepath:
            self.filepath = filepath
            self.sample_rate, self.original_audio_data = audio_utils.load_audio(self.filepath)
            if self.original_audio_data is not None:
                self.original_filesize_kb = os.path.getsize(self.filepath) / 1024
                self.song_length_ms = (len(self.original_audio_data) / self.sample_rate) * 1000
                self.create_editor_ui()
                self.stacked_widget.setCurrentIndex(1)

    def create_editor_ui(self):
        self.eq_sliders = {}
        self.compression_slider = {}

        editor_page = QWidget()
        main_layout = QHBoxLayout(editor_page)

        self.controls_stack = QStackedWidget()
        eq_controls_page = self.setup_eq_controls()
        compression_controls_page = self.setup_compression_controls()
        self.controls_stack.addWidget(eq_controls_page)
        self.controls_stack.addWidget(compression_controls_page)

        right_column = QVBoxLayout()
        self.waveform_view = QGraphicsView()
        self.waveform_scene = QGraphicsScene()
        self.waveform_view.setScene(self.waveform_scene)
        self.base_wave_item = QGraphicsPathItem()
        self.eq_wave_item = QGraphicsPathItem()
        self.waveform_scene.addItem(self.base_wave_item)
        self.waveform_scene.addItem(self.eq_wave_item)

        playback_controls = self.setup_playback_controls()

        self.nav_stack = QStackedWidget()
        eq_nav = self.setup_eq_nav()
        comp_nav = self.setup_comp_nav()
        self.nav_stack.addWidget(eq_nav)
        self.nav_stack.addWidget(comp_nav)

        right_column.addWidget(self.waveform_view)
        right_column.addLayout(playback_controls)
        right_column.addWidget(self.nav_stack)

        main_layout.addWidget(self.controls_stack, 1)
        main_layout.addLayout(right_column, 2)

        self.stacked_widget.addWidget(editor_page)
        self.update_waveform_preview()

    def setup_eq_controls(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Equalizer");
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.setSpacing(20)
        eq_slider_names = ['bass', 'mid', 'treble']
        for name in eq_slider_names:
            self.eq_sliders[name] = {}
            self.eq_sliders[name]['label'] = QLabel(f"{name.capitalize()}: 1.00x")
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100);
            slider.setValue(25)
            slider.valueChanged.connect(self.on_slider_change)  # Connect to the new handler
            layout.addWidget(self.eq_sliders[name]['label'])
            layout.addWidget(slider)
            self.eq_sliders[name]['slider'] = slider
        layout.addStretch()
        return page

    def setup_compression_controls(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Compression");
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        layout.setSpacing(20)

        self.compression_slider['label'] = QLabel("Compression: 0%")
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100);
        slider.setValue(0)
        slider.valueChanged.connect(self.on_slider_change)  # Connect to the new handler

        self.file_size_label_orig = QLabel(f"Original Size: {self.original_filesize_kb:.1f} KB")
        self.file_size_label_est = QLabel("Estimated New Size: ...")

        layout.addWidget(self.compression_slider['label'])
        layout.addWidget(slider)
        layout.addSpacing(30)
        layout.addWidget(self.file_size_label_orig)
        layout.addWidget(self.file_size_label_est)
        self.compression_slider['slider'] = slider
        layout.addStretch()
        self.update_compression_labels()
        return page

    def setup_playback_controls(self):
        layout = QVBoxLayout()
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel(time.strftime('%M:%S', time.gmtime(self.song_length_ms / 1000)))
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)

        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.sliderMoved.connect(self.seek_playback)

        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.setFixedSize(100, 40)
        self.play_pause_button.clicked.connect(self.toggle_play_pause)

        play_button_layout = QHBoxLayout()
        play_button_layout.addStretch()
        play_button_layout.addWidget(self.play_pause_button)
        play_button_layout.addStretch()

        layout.addLayout(time_layout)
        layout.addWidget(self.progress_slider)
        layout.addLayout(play_button_layout)
        return layout

    def setup_eq_nav(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        next_button = QPushButton("Next →")
        next_button.setObjectName("AccentButton")
        next_button.clicked.connect(self.go_to_compression)
        layout.addStretch()
        layout.addWidget(next_button)
        return page

    def setup_comp_nav(self):
        page = QWidget()
        layout = QHBoxLayout(page)
        back_button = QPushButton("← Back")
        save_button = QPushButton("Save File")
        save_button.setObjectName("AccentButton")
        back_button.clicked.connect(self.go_to_eq)
        save_button.clicked.connect(self.save_final_audio)
        layout.addWidget(back_button)
        layout.addStretch()
        layout.addWidget(save_button)
        return page

    # --- THIS IS THE NEW FUNCTION ---
    def on_slider_change(self):
        """Called whenever any slider is moved."""
        self.settings_changed_since_play = True

        # If the user changes a setting while music is playing, pause it.
        if self.is_playing:
            pygame.mixer.music.pause()
            self.playback_timer.stop()
            self.is_playing = False
            self.is_paused = True
            self.play_pause_button.setText("Play")

        # Update the UI visuals as before
        if self.controls_stack.currentIndex() == 0:
            self.update_eq_labels_and_waveform()
        else:
            self.update_compression_labels()

    def update_eq_labels_and_waveform(self):
        for name, data in self.eq_sliders.items():
            value = data['slider'].value()
            data['label'].setText(f"{name.capitalize()}: {(value / 100.0) * 4.0:.2f}x")
        self.update_waveform_preview()

    def update_compression_labels(self):
        value = self.compression_slider['slider'].value()
        self.compression_slider['label'].setText(f"Compression: {value}%")
        estimated_size = self.original_filesize_kb * (1 - (value / 100.0))
        self.file_size_label_est.setText(f"Estimated New Size: {estimated_size:.1f} KB")

    def update_waveform_preview(self):
        if self.original_audio_data is None: return
        chunk_size = 2048
        start_index = len(self.original_audio_data) // 2
        chunk = self.original_audio_data[start_index: start_index + chunk_size]
        eq_settings = self.get_current_eq_settings()
        eq_chunk = audio_utils.process_audio(chunk, self.sample_rate, eq_settings, 0)
        self.draw_single_waveform(self.base_wave_item, chunk, QColor("#555555"))
        self.draw_single_waveform(self.eq_wave_item, eq_chunk, QColor("#ff007f"))
        self.waveform_view.fitInView(self.waveform_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def draw_single_waveform(self, path_item, audio_chunk, color):
        path = QPainterPath()
        if audio_chunk is None or len(audio_chunk) == 0: return
        num_samples = len(audio_chunk)
        max_amp = np.max(np.abs(audio_chunk)) if np.max(np.abs(audio_chunk)) > 0 else 1.0
        path.moveTo(0, 0)
        for i in range(num_samples):
            x = (i / num_samples) * 400
            y = -(audio_chunk[i] / max_amp) * 100
            path.lineTo(x, y)
        pen = QPen(color, 2)
        path_item.setPath(path)
        path_item.setPen(pen)

    def go_to_compression(self):
        self.stop_playback()
        eq_settings = self.get_current_eq_settings()
        self.eq_audio_data = audio_utils.process_audio(self.original_audio_data, self.sample_rate, eq_settings, 0)
        self.controls_stack.setCurrentIndex(1)
        self.nav_stack.setCurrentIndex(1)

    def go_to_eq(self):
        self.stop_playback()
        self.controls_stack.setCurrentIndex(0)
        self.nav_stack.setCurrentIndex(0)

    def get_current_eq_settings(self):
        return {
            'bass': (self.eq_sliders['bass']['slider'].value() / 100.0) * 4.0,
            'mid': (self.eq_sliders['mid']['slider'].value() / 100.0) * 4.0,
            'treble': (self.eq_sliders['treble']['slider'].value() / 100.0) * 4.0,
        }

    # --- Playback Logic ---

    def toggle_play_pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.playback_timer.stop()
            self.is_playing = False
            self.is_paused = True
            self.play_pause_button.setText("Play")
        else:
            if self.is_paused and not self.settings_changed_since_play:
                pygame.mixer.music.unpause()
            else:
                self.start_playback(start_ms=self.playback_pos_ms)

            self.is_playing = True
            self.is_paused = False
            self.playback_timer.start()
            self.play_pause_button.setText("Pause")

    def start_playback(self, start_ms=0):
        if self.controls_stack.currentIndex() == 0:
            data_to_process = self.original_audio_data
            eq_settings = self.get_current_eq_settings()
            compression_ratio = 0
        else:
            data_to_process = self.eq_audio_data
            eq_settings = None
            compression_ratio = self.compression_slider['slider'].value() / 100.0

        processed_data = audio_utils.process_audio(data_to_process, self.sample_rate, eq_settings, compression_ratio)

        if processed_data is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
                self.temp_preview_file = fp.name
                wavfile.write(self.temp_preview_file, self.sample_rate, processed_data)

            pygame.mixer.music.load(self.temp_preview_file)
            pygame.mixer.music.play(start=(start_ms / 1000.0))

            self.playback_start_offset_ms = start_ms
            self.playback_timer.start()
            self.play_pause_button.setText("Pause")
            self.is_playing = True
            self.is_paused = False
            self.settings_changed_since_play = False

    def update_progress(self):
        if self.is_playing:
            elapsed_time = pygame.mixer.music.get_pos()
            self.playback_pos_ms = self.playback_start_offset_ms + elapsed_time
            if self.playback_pos_ms >= self.song_length_ms:
                self.stop_playback(song_finished=True)
                return
            self.current_time_label.setText(time.strftime('%M:%S', time.gmtime(self.playback_pos_ms / 1000)))
            self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(int((self.playback_pos_ms / self.song_length_ms) * 100))
            self.progress_slider.blockSignals(False)

    def stop_playback(self, song_finished=False):
        pygame.mixer.music.stop()
        self.playback_timer.stop()
        self.is_playing = False
        self.is_paused = False
        self.play_pause_button.setText("Play")
        if song_finished:
            self.playback_pos_ms = 0
            self.update_progress()

    def seek_playback(self, value):
        seek_ms = self.song_length_ms * (value / 100.0)
        self.playback_pos_ms = seek_ms
        self.start_playback(start_ms=self.playback_pos_ms)

    def save_final_audio(self):
        self.stop_playback()
        compression_ratio = self.compression_slider['slider'].value() / 100.0
        final_data = audio_utils.process_audio(self.eq_audio_data, self.sample_rate, None, compression_ratio)
        if final_data is not None:
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Processed File", os.path.basename(self.filepath),
                                                       "WAV Files (*.wav)")
            if save_path:
                wavfile.write(save_path, self.sample_rate, final_data)

    def closeEvent(self, event):
        if self.temp_preview_file:
            try:
                os.remove(self.temp_preview_file)
            except OSError as e:
                print(f"Error removing temp file: {e}")
        super().closeEvent(event)
