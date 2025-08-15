

# **Python FFT Audio Editor**

A sophisticated audio editing application built with Python and PyQt6 for **macOS**. It provides a modern, two-stage interface for applying equalization and compression to .wav files, featuring a real-time waveform visualizer.

### **Demo**

A screen recording of the application in action. The demo showcases the fluid two-column UI, the live waveform visualizer reacting to slider adjustments, and the seamless audio playback controls.

\[A GIF or short video\]

## **About The Project**

This is a desktop utility that allows users to apply common audio mastering effects to .wav files. The application's modern and responsive user interface is built with the industry-standard **PyQt6** framework, while the audio playback is handled by the reliable **Pygame Mixer** engine.

The core of the application is its use of the **Fast Fourier Transform (FFT)** to deconstruct audio signals into their constituent frequencies. This allows for precise, mathematical manipulation of the sound before it is reconstructed using an Inverse FFT.

### **Key Features**

* **Modern, Professional UI:** A sleek, dark-themed interface built with PyQt6, featuring a two-column layout and a multi-page workflow for a clean user experience.  
* **Live Waveform Visualizer:** Get immediate visual feedback on your EQ adjustments. The UI displays both the original and the processed waveform in real-time as you move the sliders.  
* **Extreme EQ Control:** Adjust Bass, Mid, and Treble frequencies with a powerful 0x to 4x gain multiplier.  
* **Full Playback Controls:** A complete audio playback system with play, pause, and a draggable progress bar to seek to any part of the song.  
* **Lossy Compression:** Reduce file size by intelligently removing the quietest, least perceptible frequency components.  
* **File Size Estimation:** See an estimate of the final file size in real-time as you adjust the compression level.


### **Built With**

This project was built using the following technologies:

* [Python](https://www.python.org/)  
* [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for the modern, professional GUI  
* [Pygame](https://www.pygame.org/) for the reliable audio playback engine  
* [NumPy](https://numpy.org/) for high-performance numerical and FFT calculations  
* [SciPy](https://scipy.org/) for reading and writing .wav files

## **Getting Started**

Follow these instructions to get a local copy up and running on your machine.

### **Prerequisites**

This application is designed for **macOS** and requires **Python 3.9** or newer.

* **Install Python:** If you don't have it, you can install it via [Homebrew](https://brew.sh/):  
  brew install python

### **Installation**

1. **Clone the repository:**  
   git clone \[https://github.com/your\_username/waveshaper.git\](https://github.com/your\_username/waveshaper.git)  
   cd waveshaper

2. **Create a Virtual Environment:** It's best practice to create a virtual environment to manage project dependencies.  
   python3 \-m venv venv  
   source venv/bin/activate

3. **Install Dependencies:** Install all the required libraries using pip.  
   pip install PyQt6 pygame numpy scipy

## **How to Run**

The application can be run directly from the main.py script. The file dialog is now integrated into the application's startup sequence.

**To run the application, execute the main.py file:**

python3 main.py

This will first launch the application window. Clicking the "Load .wav File" button will open a native file dialog, and upon selecting a file, you will be taken to the main editor interface.

## **Future Improvements**

This project serves as a strong foundation for a more feature-rich audio tool.

* **Real-Time** Audio **Pipeline:** Re-architect the audio engine using a library like sounddevice to apply effects to a live audio stream. This would allow the sound to change instantly as sliders are moved, without needing to press "Play" again.  
* **Additional Audio Effects:** Implement more effects like Reverb, Delay, or a Limiter.  
* **Preset System:** Add the ability to save and load EQ and compression settings.  
* **Cross-Platform Support:** While PyQt is cross-platform, the audio playback and file system interactions could be further tested and refined for Windows and Linux.
