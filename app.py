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
    def __init__(self):
        pygame.init()
        pygame.font.init()
        # We initialize the mixer later, only when needed

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("WaveShaper: Audio Editor")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 36)
        self.small_font = pygame.font.SysFont("Arial", 18)

        # --- State Management ---
        # This is the new, crucial part. It controls which screen is showing.
        self.app_state = "welcome"  # Can be 'welcome' or 'editor'

        self.running = True
        self.filepath = ""
        self.status_message = "Load a .wav file to begin."
        self.is_previewing = False
        self.preview_sound = None

        self.sliders = {}
        self.active_slider = None

        self.load_assets()
        # We create UI elements for the editor screen later
        self.create_welcome_ui()

    def load_assets(self):
        try:
            self.bg_image = pygame.image.load(get_asset_path("background.png")).convert()
            self.btn_load_img = pygame.image.load(get_asset_path("button_load.png")).convert_alpha()
            self.btn_save_img = pygame.image.load(get_asset_path("button_save.png")).convert_alpha()
            self.btn_preview_img = pygame.image.load(get_asset_path("button_preview.png")).convert_alpha()
            self.slider_bar_img = pygame.image.load(get_asset_path("slider_bar.png")).convert_alpha()
            self.slider_knob_img = pygame.image.load(get_asset_path("slider_knob.png")).convert_alpha()
        except pygame.error as e:
            print(f"FATAL ERROR: Could not load an asset. Error: {e}")
            self.running = False

    def create_welcome_ui(self):
        """Creates the single button for the welcome screen."""
        self.welcome_load_button_rect = self.btn_load_img.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

    def create_editor_ui(self):
        """Creates all the buttons and sliders for the main editor screen."""
        self.btn_load_rect = self.btn_load_img.get_rect(topleft=(50, 50))
        self.btn_preview_rect = self.btn_preview_img.get_rect(topleft=(50, 120))
        self.btn_save_rect = self.btn_save_img.get_rect(topleft=(50, 190))

        slider_names = ['bass', 'mid', 'treble', 'compression']
        start_y = 300
        for i, name in enumerate(slider_names):
            y_pos = start_y + i * 70
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
        """The main application loop that now checks the app_state."""
        while self.running:
            # Call the correct event handler and draw function based on the state
            if self.app_state == "welcome":
                self.handle_events_welcome()
                self.draw_welcome_screen()
            elif self.app_state == "editor":
                self.handle_events_editor()
                self.draw_editor_screen()

            self.clock.tick(FPS)
        pygame.quit()

    def handle_events_welcome(self):
        """Only handles events for the welcome screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.welcome_load_button_rect.collidepoint(event.pos):
                    # --- This is the fix for the crash ---
                    # We call Tkinter *before* the main editor loop is active.
                    filepath = audio_utils.select_file()
                    if filepath:
                        self.filepath = filepath
                        # If a file was chosen, set up the editor and switch states
                        self.status_message = f"Loaded: {os.path.basename(self.filepath)}"
                        self.create_editor_ui()
                        self.app_state = "editor"

    def handle_events_editor(self):
        """Handles all events for the main editor screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.btn_load_rect.collidepoint(event.pos):
                    if self.is_previewing: self.stop_preview()
                    new_filepath = audio_utils.select_file()
                    if new_filepath:
                        self.filepath = new_filepath
                        self.status_message = f"Loaded: {os.path.basename(self.filepath)}"

                elif self.btn_preview_rect.collidepoint(event.pos):
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
        self.draw_editor_screen()
        pygame.display.flip()

        eq_settings, compression_ratio = self.get_current_settings()
        sample_rate, processed_data = audio_utils.process_audio(self.filepath, eq_settings, compression_ratio)

        if processed_data is not None:
            pygame.mixer.quit()
            pygame.mixer.init(frequency=sample_rate)
            self.preview_sound = pygame.s.Sound(processed_data)
            self.preview_sound.play(loops=-1)
            self.is_previewing = True
            self.status_message = "Previewing... (Click Preview to stop)"
        else:
            self.status_message = "Error: Audio processing failed."

    def stop_preview(self):
        if self.preview_sound:
            self.preview_sound.stop()
        self.is_previewing = False
        self.status_message = "Preview stopped."

    def process_and_save(self):
        if self.is_previewing: self.stop_preview()
        self.status_message = "Processing to save..."
        self.draw_editor_screen()
        pygame.display.flip()
        eq_settings, compression_ratio = self.get_current_settings()
        sample_rate, processed_data = audio_utils.process_audio(self.filepath, eq_settings, compression_ratio)
        if processed_data is not None:
            save_path = audio_utils.save_file()
            if save_path:
                wavfile.write(save_path, sample_rate, processed_data)
                self.status_message = f"Saved to {os.path.basename(save_path)}"
            else:
                self.status_message = "Save cancelled."
        else:
            self.status_message = "Error: Audio processing failed."

    def draw_welcome_screen(self):
        """Draws only the elements for the welcome screen."""
        self.screen.blit(self.bg_image, (0, 0))
        # Draw a title
        title_text = self.font.render("WaveShaper Audio Editor", True, COLOR_TEXT)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 100))
        self.screen.blit(title_text, title_rect)
        # Draw the central load button
        self.screen.blit(self.btn_load_img, self.welcome_load_button_rect)
        pygame.display.flip()

    def draw_editor_screen(self):
        """Draws the main editor UI."""
        self.screen.blit(self.bg_image, (0, 0))
        self.screen.blit(self.btn_load_img, self.btn_load_rect)
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
