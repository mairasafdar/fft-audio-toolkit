import pygame
import os
import audio_utils
from scipy.io import wavfile
import numpy as np
import tempfile

# --- Constants ---
# Increased width for the new two-column layout
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 700
FPS = 60
COLOR_TEXT = (230, 230, 230)
COLOR_BG_TEXT = (50, 50, 50)
COLOR_PROGRESS_BG = (70, 70, 70)
COLOR_PROGRESS_FG = (50, 150, 255)
COLOR_WAVEFORM_BASE = (100, 100, 100)
COLOR_WAVEFORM_EQ = (50, 150, 255)

# Define a clear starting point for the right-side UI column
RIGHT_COLUMN_X = 600


def get_asset_path(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'assets', filename)


class AudioApp:
    def __init__(self, input_filepath):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("WaveShaper: Audio Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)

        self.app_state = "editor_eq"
        self.running = True

        self.filepath = input_filepath
        self.sample_rate, self.original_audio_data = audio_utils.load_audio(self.filepath)
        self.eq_audio_data = None
        self.original_filesize_kb = os.path.getsize(self.filepath) / 1024 if self.filepath else 0

        self.is_playing = False
        self.is_paused = False
        self.playback_pos_ms = 0
        self.song_length_ms = (
                                          len(self.original_audio_data) / self.sample_rate) * 1000 if self.original_audio_data is not None else 0

        self.active_slider = None
        self.status_message = f"Editing EQ for: {os.path.basename(self.filepath)}"
        self.temp_preview_file = None

        self.load_assets()
        self.create_ui()

    def load_assets(self):
        try:
            self.bg_image = pygame.image.load(get_asset_path("background.png")).convert()
            self.btn_play_img = pygame.image.load(get_asset_path("button_play.png")).convert_alpha()
            self.btn_pause_img = pygame.image.load(get_asset_path("button_pause.png")).convert_alpha()
            self.btn_save_img = pygame.image.load(get_asset_path("button_save.png")).convert_alpha()
            self.btn_next_img = pygame.image.load(get_asset_path("button_next.png")).convert_alpha()
            self.btn_back_img = pygame.image.load(get_asset_path("button_back.png")).convert_alpha()
            self.slider_bar_img = pygame.image.load(get_asset_path("slider_bar.png")).convert_alpha()
            self.slider_knob_img = pygame.image.load(get_asset_path("slider_knob.png")).convert_alpha()
        except pygame.error as e:
            print(f"FATAL ERROR: Could not load an asset. Error: {e}")
            self.running = False

    def create_ui(self):
        # --- Common UI Elements ---
        self.progress_bar_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, SCREEN_WIDTH - 100, 20)
        self.btn_play_pause_rect = self.btn_play_img.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50))

        # --- EQ Screen UI (Left Column) ---
        self.eq_sliders = {}
        eq_slider_names = ['bass', 'mid', 'treble']
        for i, name in enumerate(eq_slider_names):
            y_pos = 200 + i * 100
            bar_rect = self.slider_bar_img.get_rect(topleft=(50, y_pos))
            knob_rect = self.slider_knob_img.get_rect(center=(bar_rect.centerx, bar_rect.centery))
            self.eq_sliders[name] = {'name': name.capitalize(), 'bar_rect': bar_rect, 'knob_rect': knob_rect,
                                     'ratio': 0.25}

        # --- Compression Screen UI (Left Column) ---
        y_pos = 200
        bar_rect = self.slider_bar_img.get_rect(topleft=(50, y_pos))
        knob_rect = self.slider_knob_img.get_rect(center=(bar_rect.left, bar_rect.centery))
        self.compression_slider = {'name': 'Compression', 'bar_rect': bar_rect, 'knob_rect': knob_rect, 'ratio': 0.0}

        # --- Right-side column UI ---
        self.visualizer_rect = pygame.Rect(RIGHT_COLUMN_X, 80, 380, 250)
        self.btn_next_rect = self.btn_next_img.get_rect(topleft=(RIGHT_COLUMN_X, self.visualizer_rect.bottom + 50))
        self.btn_back_rect = self.btn_back_img.get_rect(topleft=(RIGHT_COLUMN_X, self.visualizer_rect.bottom + 50))
        self.btn_save_rect = self.btn_save_img.get_rect(topleft=(self.btn_back_rect.right + 20, self.btn_back_rect.top))

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        if self.temp_preview_file:
            try:
                os.remove(self.temp_preview_file)
            except OSError as e:
                print(f"Error removing temp file: {e}")
        pygame.quit()

    def handle_events(self):
        current_sliders = self.eq_sliders if self.app_state == 'editor_eq' else {'compression': self.compression_slider}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_play_pause_rect.collidepoint(event.pos):
                    self.toggle_play_pause()
                elif self.progress_bar_rect.collidepoint(event.pos):
                    self.seek_playback(event.pos[0])

                if self.app_state == 'editor_eq':
                    if self.btn_next_rect.collidepoint(event.pos):
                        self.go_to_compression()
                elif self.app_state == 'editor_compression':
                    if self.btn_back_rect.collidepoint(event.pos):
                        self.go_to_eq()
                    elif self.btn_save_rect.collidepoint(event.pos):
                        self.save_final_audio()

                for slider in current_sliders.values():
                    if slider['knob_rect'].collidepoint(event.pos):
                        self.active_slider = slider
                        break

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.active_slider = None

            if event.type == pygame.MOUSEMOTION and self.active_slider:
                bar = self.active_slider['bar_rect']
                self.active_slider['knob_rect'].centerx = max(bar.left, min(event.pos[0], bar.right))
                self.active_slider['ratio'] = (self.active_slider['knob_rect'].centerx - bar.left) / bar.width

                # --- THIS IS THE NEW FEATURE ---
                # If the user is dragging a slider while music is playing, pause it.
                if self.is_playing:
                    pygame.mixer.music.pause()
                    self.is_paused = True
                    self.is_playing = False
                    self.status_message = "Settings changed. Press Play to hear changes."

    def update(self):
        if self.is_playing and pygame.mixer.music.get_busy():
            self.playback_pos_ms += self.clock.get_time()
        elif self.is_playing and not pygame.mixer.music.get_busy():
            self.stop_playback(song_finished=True)

    def go_to_compression(self):
        self.stop_playback()
        self.status_message = "Applying EQ... please wait."
        self.draw()
        pygame.display.flip()
        eq_settings = self.get_current_eq_settings()
        self.eq_audio_data = audio_utils.process_audio(self.original_audio_data, self.sample_rate, eq_settings, 0)
        self.app_state = 'editor_compression'
        self.status_message = "Adjust compression level."

    def go_to_eq(self):
        self.stop_playback()
        self.app_state = 'editor_eq'
        self.status_message = f"Editing EQ for: {os.path.basename(self.filepath)}"

    def toggle_play_pause(self):
        # --- THIS LOGIC IS NOW FIXED ---
        # If paused, it means settings have changed. We need to re-process and play.
        if self.is_paused:
            self.start_playback(start_ms=self.playback_pos_ms)
        # If it's not playing at all, start from the beginning (or wherever the slider is).
        elif not self.is_playing:
            self.start_playback(start_ms=self.playback_pos_ms)
        # If it is currently playing, just pause it.
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.is_playing = False
            self.status_message = "Paused."

    def start_playback(self, start_ms=0):
        self.status_message = "Processing for preview..."
        self.draw()
        pygame.display.flip()

        data_to_process = self.eq_audio_data if self.app_state == 'editor_compression' else self.original_audio_data
        eq_settings = self.get_current_eq_settings() if self.app_state == 'editor_eq' else None
        compression_ratio = self.compression_slider['ratio'] if self.app_state == 'editor_compression' else 0

        processed_data = audio_utils.process_audio(data_to_process, self.sample_rate, eq_settings, compression_ratio)

        if processed_data is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as fp:
                self.temp_preview_file = fp.name
                wavfile.write(self.temp_preview_file, self.sample_rate, processed_data)

            pygame.mixer.music.load(self.temp_preview_file)
            pygame.mixer.music.play(start=(start_ms / 1000.0))
            self.is_playing = True
            self.is_paused = False
            self.playback_pos_ms = start_ms
            self.status_message = "Previewing..."
        else:
            self.status_message = "Error: Preview failed."

    def stop_playback(self, song_finished=False):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.is_paused = False
        if song_finished:
            self.playback_pos_ms = 0
            self.status_message = "Preview finished."
        else:
            self.status_message = "Preview stopped."

    def seek_playback(self, mouse_x):
        seek_ratio = (mouse_x - self.progress_bar_rect.left) / self.progress_bar_rect.width
        seek_ms = self.song_length_ms * seek_ratio
        self.stop_playback()
        self.start_playback(start_ms=seek_ms)

    def save_final_audio(self):
        self.stop_playback()
        self.status_message = "Processing final audio..."
        self.draw()
        pygame.display.flip()

        compression_ratio = self.compression_slider['ratio']
        final_data = audio_utils.process_audio(self.eq_audio_data, self.sample_rate, None, compression_ratio)

        if final_data is not None:
            directory = os.path.dirname(self.filepath)
            filename, ext = os.path.splitext(os.path.basename(self.filepath))
            save_path = os.path.join(directory, f"{filename}_final{ext}")
            try:
                wavfile.write(save_path, self.sample_rate, final_data)
                self.status_message = f"Saved to {os.path.basename(save_path)}"
            except Exception as e:
                self.status_message = f"Error saving file: {e}"
        else:
            self.status_message = "Error: Final processing failed."

    def draw(self):
        self.screen.blit(self.bg_image, (0, 0))

        if self.app_state == 'editor_eq':
            self.draw_eq_screen()
        elif self.app_state == 'editor_compression':
            self.draw_compression_screen()

        self.draw_progress_bar()
        play_pause_btn = self.btn_pause_img if self.is_playing or self.is_paused else self.btn_play_img
        self.screen.blit(play_pause_btn, self.btn_play_pause_rect)
        status_surf = self.small_font.render(self.status_message, True, COLOR_TEXT, COLOR_BG_TEXT)
        self.screen.blit(status_surf, (20, SCREEN_HEIGHT - 30))

        pygame.display.flip()

    def draw_eq_screen(self):
        title = self.title_font.render("Step 1: Equalizer", True, COLOR_TEXT)
        self.screen.blit(title, (50, 20))
        self.draw_sliders(self.eq_sliders)
        self.screen.blit(self.btn_next_img, self.btn_next_rect)
        self.draw_waveform_visualizer()

    def draw_compression_screen(self):
        title = self.title_font.render("Step 2: Compression", True, COLOR_TEXT)
        self.screen.blit(title, (50, 20))
        self.draw_sliders({'compression': self.compression_slider})
        self.screen.blit(self.btn_back_img, self.btn_back_rect)
        self.screen.blit(self.btn_save_img, self.btn_save_rect)
        self.draw_file_size_info()

    def draw_sliders(self, sliders_to_draw):
        for slider in sliders_to_draw.values():
            self.screen.blit(self.slider_bar_img, slider['bar_rect'])
            self.screen.blit(self.slider_knob_img, slider['knob_rect'])
            label_text = self.font.render(slider['name'], True, COLOR_TEXT)
            self.screen.blit(label_text, (slider['bar_rect'].left, slider['bar_rect'].top - 35))

            ratio = slider['ratio']
            if slider['name'] != 'Compression':
                value_str = f"{ratio * 4.0:.2f}x"
            else:
                value_str = f"{ratio * 100:.0f}%"
            value_text = self.small_font.render(value_str, True, COLOR_TEXT)
            self.screen.blit(value_text, (slider['bar_rect'].right + 20, slider['bar_rect'].centery - 10))

    def draw_progress_bar(self):
        pygame.draw.rect(self.screen, COLOR_PROGRESS_BG, self.progress_bar_rect)
        if self.song_length_ms > 0:
            progress_ratio = self.playback_pos_ms / self.song_length_ms
            progress_width = self.progress_bar_rect.width * progress_ratio
            progress_rect = pygame.Rect(self.progress_bar_rect.left, self.progress_bar_rect.top, progress_width,
                                        self.progress_bar_rect.height)
            pygame.draw.rect(self.screen, COLOR_PROGRESS_FG, progress_rect)

    def draw_waveform_visualizer(self):
        chunk_size = 2048
        if len(self.original_audio_data) < chunk_size: return
        start_index = len(self.original_audio_data) // 2
        chunk = self.original_audio_data[start_index: start_index + chunk_size]

        eq_settings = self.get_current_eq_settings()
        eq_chunk = audio_utils.process_audio(chunk, self.sample_rate, eq_settings, 0)
        if eq_chunk is None: return

        self.draw_single_waveform(self.visualizer_rect, chunk, COLOR_WAVEFORM_BASE)
        self.draw_single_waveform(self.visualizer_rect, eq_chunk, COLOR_WAVEFORM_EQ)

    def draw_single_waveform(self, rect, audio_chunk, color):
        points = []
        num_samples = len(audio_chunk)
        max_amp = np.max(np.abs(audio_chunk)) if np.max(np.abs(audio_chunk)) > 0 else 1

        for i in range(num_samples):
            x = rect.left + (i / num_samples) * rect.width
            y = rect.centery - (audio_chunk[i] / max_amp) * (rect.height / 2)
            points.append((x, y))

        if len(points) > 1:
            pygame.draw.aalines(self.screen, color, False, points)

    def draw_file_size_info(self):
        compression_ratio = self.compression_slider['ratio']
        estimated_new_size = self.original_filesize_kb * (1 - compression_ratio)
        orig_text = self.font.render(f"Original Size: {self.original_filesize_kb:.2f} KB", True, COLOR_TEXT)
        est_text = self.font.render(f"Estimated New Size: {estimated_new_size:.2f} KB", True, COLOR_TEXT)
        self.screen.blit(orig_text, (RIGHT_COLUMN_X, 200))
        self.screen.blit(est_text, (RIGHT_COLUMN_X, 240))

    def get_current_eq_settings(self):
        return {
            'bass': self.eq_sliders['bass']['ratio'] * 4.0,
            'mid': self.eq_sliders['mid']['ratio'] * 4.0,
            'treble': self.eq_sliders['treble']['ratio'] * 4.0,
        }
