import numpy as np
from scipy.io import wavfile
# Using the standard, most common import style for PySimpleGUI
import PySimpleGUI as sg


def select_file():
    """Opens a file dialog to select a .wav file using the modern PySimpleGUI API."""
    # Define the layout for our small pop-up window
    layout = [
        [sg.Text("Please select an audio file")],
        # The Input element will show the path, FileBrowse opens the dialog
        [sg.Input(key='-FILE-'), sg.FileBrowse(file_types=(("WAV Files", "*.wav"),))],
        [sg.OK(), sg.Cancel()]
    ]

    # Create the window
    window = sg.Window('Select WAV File', layout)

    filepath = None
    # This is the event loop for our small pop-up window
    while True:
        event, values = window.read()
        # If user closes window or clicks Cancel
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        # If user clicks OK, we get the filepath from the Input element
        if event == 'OK':
            filepath = values['-FILE-']
            break

    window.close()
    return filepath


def save_file():
    """Opens a file dialog to save a .wav file using the modern PySimpleGUI API."""
    layout = [
        [sg.Text("Save processed audio as...")],
        [sg.Input(key='-FILE-'), sg.FileSaveAs(file_types=(("WAV Files", "*.wav"),), default_extension=".wav")],
        [sg.OK(), sg.Cancel()]
    ]

    window = sg.Window('Save As', layout)

    filepath = None
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel':
            break
        if event == 'OK':
            filepath = values['-FILE-']
            break

    window.close()
    return filepath


def process_audio(filepath, eq_settings, compression_ratio):
    """
    Loads a .wav file, applies equalization and compression, and returns
    the new audio data. This function remains unchanged.
    """
    if not filepath:
        return None, None

    try:
        sample_rate, audio_data = wavfile.read(filepath)
        if audio_data.ndim == 2:
            audio_data = audio_data.mean(axis=1)
        audio_data = audio_data.astype(np.float32)

        fft_data = np.fft.rfft(audio_data)
        fft_freqs = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)

        bass_band = (fft_freqs < 250)
        mid_band = (fft_freqs >= 250) & (fft_freqs < 4000)
        treble_band = (fft_freqs >= 4000)

        fft_data[bass_band] *= eq_settings['bass']
        fft_data[mid_band] *= eq_settings['mid']
        fft_data[treble_band] *= eq_settings['treble']

        if compression_ratio > 0:
            magnitudes = np.abs(fft_data)
            threshold_index = int(len(magnitudes) * compression_ratio)
            sorted_magnitudes = np.sort(magnitudes)
            threshold_value = sorted_magnitudes[threshold_index]
            fft_data[magnitudes < threshold_value] = 0

        processed_audio = np.fft.irfft(fft_data)

        max_val = np.max(np.abs(processed_audio))
        if max_val > 0:
            normalized_audio = processed_audio / max_val * 32767
        else:
            normalized_audio = processed_audio

        final_audio = normalized_audio.astype(np.int16)

        return sample_rate, final_audio

    except Exception as e:
        print(f"Error during audio processing: {e}")
        return None, None
