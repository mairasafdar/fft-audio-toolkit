import sys
import os
from app import AudioApp

# This is the main entry point of our program
if __name__ == "__main__":
    # Check if the user provided a filepath when running the script
    if len(sys.argv) < 2:
        print("Error: You must provide a path to a .wav file.")
        print("Usage: python3 main.py /path/to/your/audio.wav")
        # A simple way to show how to use it is to drag and drop a file
        # into the terminal after typing 'python3 main.py '.
        sys.exit(1)  # Exit the program if no file is provided

    filepath = sys.argv[1]

    # Check if the provided file exists
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        sys.exit(1)

    # Create an instance of our application, passing the filepath to it
    audio_editor_app = AudioApp(filepath)

    # Run the application's main loop
    audio_editor_app.run()
