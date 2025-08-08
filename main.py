# Import the application class from our app.py file
from app import AudioApp

# This is the main entry point of our program
if __name__ == "__main__":
    # 1. Create an instance of our application
    audio_editor_app = AudioApp()

    # 2. Run the application's main loop
    audio_editor_app.run()
