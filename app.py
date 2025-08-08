import pygame
import os
import audio_utils
from scipy.io import wavfile

# --- Constants ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
COLOR_TEXT = (230, 230, 230)
COLOR_BG_TEXT = (50, 50, 50)


def get_asset_path(filename):
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'assets', filename)


class AudioApp:
    def __init__(self, input_filepath):
        """The app now takes the filepath as an argument when it's created."""
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("WaveShaper: Audio Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)

        self.running = True
        self.filepath = input_filepath
        self.status_message = f"Editing: {os.path.basename(self.filepath)}"
        self.is_previewing = False
        self.preview_sound = None

        self.sliders = {}
        self.active_slider = None

        self.load_assets()
        self.create_editor_ui()

    def load_assets(self):
        try:
            self.bg_image = pygame.image.load(get_asset_path("background.png")).convert()
            # We no longer need the 'load' button image
            self.btn_save_img = pygame.image.load(get_asset_path("button_save.png")).convert_alpha()
            self.btn_preview_img = pygame.image.load(get_asset_path("button_preview.png")).convert_alpha()
            self.slider_bar_img = pygame.image.load(get_asset_path("slider_bar.png")).convert_alpha()
            self.slider_knob_img = pygame.image.load(get_asset_path("slider_knob.png")).convert_alpha()
        except pygame.error as e:
            print(f"FATAL ERROR: Could not load an asset. Error: {e}")
            self.running = False

    def create_editor_ui(self):
        """Creates the UI for the editor screen."""
        self.btn_preview_rect = self.btn_preview_img.get_rect(topleft=(50, 50))
        self.btn_save_rect = self.btn_save_img.get_rect(topleft=(50, 120))

        slider_names = ['bass', 'mid', 'treble', 'compression']
        start_y = 250
        for i, name in enumerate(slider_names):
            y_pos = start_y + i * 80
            bar_rect = self.slider_bar_img.get_rect(topleft=(150, y_pos))
            initial_ratio = 0.5 if name != 'compression' else 0.0
            knob_x = bar_rect.left + (initial_ratio * bar_rect.width)
            knob_rect = self.slider_knob_img.get_rect(center=(knob_x, bar_rect.centery))

            self.sliders[name] = {
                'name': name.capitalize(),
                'bar_rect': bar_rect,
                'knob_rect': knob_rect,
                'ratio': initial_ratio
            }

    def run(self):
        while self.running:
            self.handle_events()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_preview_rect.collidepoint(event.pos):
                    if self.is_previewing:
                        self.stop_preview()
                    else:
                        self.process_and_preview()

                elif self.btn_save_rect.collidepoint(event.pos):
                    self.process_and_save()

                for slider in self.sliders.values():
                    if slider['knob_rect'].collidepoint(event.pos):
                        self.active_slider = slider
                        break

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.active_slider = None

            if event.type == pygame.MOUSEMOTION and self.active_slider:
                mouse_x = event.pos[0]
                bar = self.active_slider['bar_rect']
                knob = self.active_slider['knob_rect']
                knob.centerx = max(bar.left, min(mouse_x, bar.right))
                self.active_slider['ratio'] = (knob.centerx - bar.left) / bar.width

    def get_current_settings(self):
        eq_settings = {
            'bass': self.sliders['bass']['ratio'] * 2.0,
            'mid': self.sliders['mid']['ratio'] * 2.0,
            'treble': self.sliders['treble']['ratio'] * 2.0,
        }
        compression_ratio = self.sliders['compression']['ratio']
        return eq_settings, compression_ratio

    def process_and_preview(self):
        self.status_message = "Processing for preview..."
        self.draw()
        pygame.display.flip()
        eq_settings, compression_ratio = self.get_current_settings()
        sample_rate, processed_data = audio_utils.process_audio(self.filepath, eq_settings, compression_ratio)
        if processed_data is not None:
            pygame.mixer.quit()
            # --- THIS IS THE FIX ---
            # Be explicit about the audio format:
            # frequency = sample_rate (e.g., 44100)
            # size = -16 (16-bit audio, the standard for WAV)
            # channels = 1 (mono audio)
            pygame.mixer.init(frequency=sample_rate, size=-16, channels=1)
            self.preview_sound = pygame.mixer.Sound(buffer=processed_data)
            self.preview_sound.play(loops=-1)
            self.is_previewing = True
            self.status_message = "Previewing... (Click Preview to stop)"
        else:
            self.status_message = "Error: Audio processing failed."

    def stop_preview(self):
        if self.preview_sound: self.preview_sound.stop()
        self.is_previewing = False
        self.status_message = f"Editing: {os.path.basename(self.filepath)}"

    def process_and_save(self):
        if self.is_previewing: self.stop_preview()
        self.status_message = "Processing to save..."
        self.draw()
        pygame.display.flip()
        eq_settings, compression_ratio = self.get_current_settings()
        sample_rate, processed_data = audio_utils.process_audio(self.filepath, eq_settings, compression_ratio)
        if processed_data is not None:
            # Create a new filename automatically
            directory = os.path.dirname(self.filepath)
            filename, ext = os.path.splitext(os.path.basename(self.filepath))
            save_path = os.path.join(directory, f"{filename}_processed{ext}")

            try:
                wavfile.write(save_path, sample_rate, processed_data)
                self.status_message = f"Successfully saved to {os.path.basename(save_path)}"
            except Exception as e:
                self.status_message = f"Error saving file: {e}"
        else:
            self.status_message = "Error: Audio processing failed."

    def draw(self):
        self.screen.blit(self.bg_image, (0, 0))
        self.screen.blit(self.btn_preview_img, self.btn_preview_rect)
        self.screen.blit(self.btn_save_img, self.btn_save_rect)
        for slider in self.sliders.values():
            self.screen.blit(self.slider_bar_img, slider['bar_rect'])
            self.screen.blit(self.slider_knob_img, slider['knob_rect'])
            label_text = self.font.render(slider['name'], True, COLOR_TEXT)
            label_rect = label_text.get_rect(centery=slider['bar_rect'].centery, right=slider['bar_rect'].left - 20)
            self.screen.blit(label_text, label_rect)
            ratio = slider['ratio']
            value_str = f"{ratio * 2:.1f}x" if slider['name'] != 'Compression' else f"{ratio * 100:.0f}%"
            value_text = self.small_font.render(value_str, True, COLOR_TEXT)
            value_rect = value_text.get_rect(centery=slider['bar_rect'].centery, left=slider['bar_rect'].right + 20)
            self.screen.blit(value_text, value_rect)
        status_surf = self.font.render(self.status_message, True, COLOR_TEXT, COLOR_BG_TEXT)
        status_rect = status_surf.get_rect(centerx=SCREEN_WIDTH / 2, bottom=SCREEN_HEIGHT - 20)
        self.screen.blit(status_surf, status_rect)
        pygame.display.flip()
