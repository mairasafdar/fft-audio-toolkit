import PySimpleGUI as sg
import subprocess
import sys
import os


# This script acts as the entry point. It opens a file dialog first,
# then launches the main Pygame application in a separate process.

def main():
    """
    Uses PySimpleGUI to get a file path and then launches the main app.
    """
    # Set a theme for the file dialog window
    sg.theme('DarkPurple1')

    # Define the layout for our file dialog window.
    # This is more robust than the simple popup.
    layout = [
        [sg.Text("Please select a .wav audio file to edit.")],
        [sg.Input(key='-FILE-'), sg.FileBrowse(file_types=(("WAV Files", "*.wav"),))],
        # The FileBrowse button is what actually opens the native macOS file picker.
        [sg.OK(), sg.Cancel()] #Ok and Cancel buttons
    ]

    window = sg.Window('AudioToolkit Launcher', layout) #Window for the layout

    filepath = None
    while True:
        #Event loop, waits for user to do something
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break # If you close the window or press Cancel, loop breaks
        if event == 'OK':
            filepath = values['-FILE-'] #if you press OK, the filepath = input
            break

    window.close()

    # If a file was successfully selected, launch the main application
    if filepath and os.path.exists(filepath):
        print(f"Launcher: File selected. Starting main application with: {filepath}")

        # We find the path to the main.py script relative to this launcher
        main_app_path = os.path.join(os.path.dirname(__file__), 'main.py')

        # We use subprocess.run to execute the command (same as you manually typing): `python3 main.py /path/to/file.wav`
        try:
            # sys.executable ensures we use the same Python interpreter as the launcher
            subprocess.run([sys.executable, main_app_path, filepath], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error launching main application: {e}")
        except FileNotFoundError:
            print(f"Error: Could not find '{sys.executable}'. Make sure Python is in your PATH.")

    else:
        print("Launcher: No file selected or file not found. Exiting.")


if __name__ == "__main__":
    main()
