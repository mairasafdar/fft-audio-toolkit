import sys
from PyQt6.QtWidgets import QApplication
# We import the new, rewritten AudioApp class
from app import AudioApp

if __name__ == "__main__":
    # This is the standard entry point for any PyQt application.
    app = QApplication(sys.argv)

    # Create an instance of our main application window.
    window = AudioApp()
    window.show()  # Show the window on the screen.

    # Start the application's main event loop.
    sys.exit(app.exec())
