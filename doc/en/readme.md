# Audio Equalizer for NVDA

Author: Daliana
Version: 1.2.0
Compatibility: NVDA 2023.1 or later
License: GNU GPL v2

This add-on provides a fully accessible 31-band graphic equalizer for NVDA on Windows. It lets you quickly adjust bass and treble on the fly, choose or create custom sound profiles, adjust stereo balance, and apply acoustic filters designed for headphones and screen reader voice clarity.

## Requirements and Setup

Audio processing is handled through Equalizer APO, a free system-wide audio engine for Windows that runs with zero latency and no distortion.

- Equalizer APO must be installed on your system.
- If it is not installed, the add-on detects your Windows architecture (32 or 64-bit) and offers to download the installer directly to your Downloads folder. Once downloaded, you can run the installer.
- You can also start the download at any time from NVDA menu > Tools > Audio Equalizer > Download and install audio engine (Equalizer APO)... or from its official website: https://sourceforge.net/projects/equalizerapo/

## Keyboard Shortcuts and Customization

To avoid colliding with NVDA native commands or other add-ons (such as System Monitor), this add-on does not assign any default keyboard shortcuts.

You can access all functions directly from NVDA menu > Tools > Audio Equalizer, or assign your favorite keystrokes from NVDA menu > Preferences > Input Gestures, under the "Ecualizador de audio" category.

Available actions include:
- Increase / decrease bass (1 dB steps).
- Increase / decrease treble (1 dB steps).
- Increase / decrease preamp (1 dB steps).
- Toggle automatic preamp to prevent clipping.
- Shift balance left or right, and center balance.
- Adjust stereo width (Mid/Side).
- Toggle mono mode and channel swap (L/R).
- Toggle loudness compensation.
- Toggle NVDA voice clarity and vocal presence boost.
- Toggle headphone acoustic filters: anti-fatigue, anti-sibilance, sub-bass, subsonic, and ground hum notch.
- Channel orientation listening test.
- Reset equalizer to flat (0 dB).
- Check for shortcut conflicts with other add-ons.

## Settings Dialog Overview

Opening settings from NVDA Menu > Tools > Audio Equalizer (or via a custom shortcut assigned in Input Gestures) opens the accessible settings window:

### Sound Profiles
Choose from tuned factory presets (Flat, Music, Studio, Movies, Gaming, Voice, Rock, Pop, Electronic, Classical, Jazz, Bass Boost, Treble Boost, Night Mode), save custom profiles, delete user profiles, or run the channel test.

### Preamp and Gain Control
Manual preamp slider from -20 dB to 0 dB, plus an automatic preamp toggle that protects against clipping when boosting EQ bands.

### Stereo and Balance
Mono toggle, channel swap (L/R), smooth balance adjustment, and stereo width slider from 0% to 200%.

### Headphone and Vocal Filters
Optional filters including low-volume Loudness compensation, NVDA voice optimization, vocal presence, anti-sibilance, anti-fatigue, anti-boxiness, ground hum notch, sub-bass boost, and subsonic high-pass filter.

### 31-Band Equalizer
Thirty-one sliders covering 20 Hz to 20 kHz in 1/3-octave steps with a -12 dB to +12 dB range.

### Tools and Diagnostics
- View Log button to inspect real-time Equalizer APO commands.
- Conflict detection tool in the NVDA Tools menu.
