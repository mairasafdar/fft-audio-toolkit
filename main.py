import sys #to read arguments from the commad line
import os #to check if file exists
from app import AudioApp #imports the main application class

# This block runs only when the script is executed directly.
if __name__ == "__main__":
    # Check if the user provided a filepath when running the script
    if len(sys.argv) < 2:
        # sys.argv is a list of words from the command that ran this script.
        # sys.argv[0] is 'main.py'
        # sys.argv[1] is the file path sent by the launcher.
        # We check if we received at least two arguments.
        print("Error: You must provide a path to a .wav file.")
        print("Usage: python3 main.py /path/to/your/audio.wav")
        # A simple way to show how to use it is to drag and drop a file
        # into the terminal after typing 'python3 main.py '.
        sys.exit(1)  # Exit the program if no file is provided

    filepath = sys.argv[1] # store file path in variable

    # Check if the provided file exists
    if not os.path.exists(filepath):
        print(f"Error: The file '{filepath}' was not found.")
        sys.exit(1)

    # Create an instance of our application, passing the filepath to it
    audio_editor_app = AudioApp(filepath)

    # This command starts the Pygame window and its main loop.
    audio_editor_app.run()
