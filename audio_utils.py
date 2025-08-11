import numpy as np
from scipy.io import wavfile #for reading wavefiles
import os


def load_audio(filepath):
    """Loads a .wav file and returns its sample rate and raw data."""
    # First, check if the file path is valid.
    if not filepath or not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        return None, None
    try:
        # wavfile.read returns two things: the sample rate (e.g., 44100 Hz)
        # and the audio data itself as a NumPy array, so can store these in two variables
        sample_rate, audio_data = wavfile.read(filepath)

        # Convert to mono and float for processing:
        # If audio_data.ndim is 2, it means the audio is stereo (2 channels).
        # We average the two channels to make it mono (1 channel).
        if audio_data.ndim == 2:
            audio_data = audio_data.mean(axis=1)
            # We convert the data to a floating-point format for accurate math.
        return sample_rate, audio_data.astype(np.float32)

    except Exception as e:
        print(f"Error loading audio file: {e}")
        return None, None


def process_audio(audio_data, sample_rate, eq_settings, compression_ratio):
    """
    Applies equalization and/or compression to raw audio data.
    Returns the final processed audio data ready for saving or playback.
    """
    if audio_data is None:
        return None

    try:
        # Perform FFT on the entire audio signal
        # This converts our sound wave (amplitude over time) into its
        # frequency components (amplitude per frequency).
        fft_data = np.fft.rfft(audio_data)

        # --- Apply Equalization if settings are provided ---
        if eq_settings:
            # We need to know the actual frequency (in Hz) for each value in fft_data.
            # rfftfreq calculates this for us.
            fft_freqs = np.fft.rfftfreq(len(audio_data), 1.0 / sample_rate)
            bass_band = (fft_freqs < 250)
            mid_band = (fft_freqs >= 250) & (fft_freqs < 4000)
            treble_band = (fft_freqs >= 4000)

            fft_data[bass_band] *= eq_settings['bass']
            fft_data[mid_band] *= eq_settings['mid']
            fft_data[treble_band] *= eq_settings['treble']

        # --- Apply Compression if ratio is greater than 0 ---
        if compression_ratio > 0:
            magnitudes = np.abs(fft_data)
            # Determine the threshold for removal
            num_to_remove = int(len(magnitudes) * compression_ratio)
            if num_to_remove > 0:
                # Find the threshold value by sorting the magnitudes
                threshold_value = np.partition(magnitudes, num_to_remove)[num_to_remove]
                # Zero out the components below the threshold
                fft_data[magnitudes < threshold_value] = 0

        # Perform Inverse FFT to get the processed audio signal back
        processed_audio = np.fft.irfft(fft_data)

        # Normalize and convert to 16-bit integers for playback/saving
        max_val = np.max(np.abs(processed_audio))
        if max_val > 0:
            normalized_audio = processed_audio / max_val * 32767
        else:
            normalized_audio = processed_audio

        return normalized_audio.astype(np.int16)

    except Exception as e:
        print(f"Error during audio processing: {e}")
        return None
