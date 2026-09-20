# Audio Equalizer for NVDA

- Author: Daliana
- Version: 1.3.0
- Compatibility: NVDA 2023.1 and later
- License: GNU GPL v2

[Leer en español](../es/readme.md)

---

## English Version

Audio Equalizer allows you to adjust sound quality in Windows directly through NVDA. You can customize bass, mids, and treble, choose from built-in profiles for music, movies, or games, adjust preamp gain, enhance NVDA voice clarity, and apply specialized headphone filters for fatigue-free listening.

### Required Audio Engine (Equalizer APO)
To apply system-wide audio effects, this add-on uses **Equalizer APO**, a free and open-source audio processing engine for Windows:
- If you don't have it installed, the add-on will guide you to download and install it automatically the first time you open it.
- You can also download it anytime from NVDA Menu > Tools > Audio Equalizer > Download and install audio engine (Equalizer APO)... or from its official website: https://sourceforge.net/projects/equalizerapo/

## Keyboard Shortcuts and Customization

To avoid conflicts with NVDA built-in commands or other add-ons (such as System Monitor), this add-on does not assign default keyboard shortcuts.

You can access all functions directly from NVDA Menu > Tools > Audio Equalizer, or assign your own preferred shortcuts in NVDA Menu > Preferences > Input Gestures under the "Audio Equalizer" category.

Available actions include:

- Increase / decrease bass (1 dB steps).
- Increase / decrease treble (1 dB steps).
- Increase / decrease preamp volume (1 dB steps).
- Toggle auto preamp on or off to prevent audio clipping.
- Adjust stereo balance left or right, and center it.
- Increase or decrease stereo width.
- Toggle mono audio mode and left/right channel swap.
- Toggle loudness compensation.
- Toggle NVDA voice clarity enhancement or vocal presence.
- Toggle headphone filters: anti-fatigue, anti-sibilance, deep bass, subsonic, and ground loop hum.
- Test headphone orientation with left, right, and center test tones.
- Reset equalizer to flat (0 dB).
- Check shortcut conflicts with other installed add-ons.

## Available Settings in the Dialog

Opening settings from NVDA Menu > Tools > Audio Equalizer displays an accessible dialog organized into the following sections:

### Sound Profiles
Choose from pre-configured profiles (Flat, Music, Studio, Movies, Gaming, Voice & Podcasts, Rock, Pop, Electronic, Classical, Jazz, Bass Boost, Treble Boost, and Night Mode). You can also save custom profiles or delete unused ones. A dedicated button allows you to test headphone orientation.

### Preamp and Gain Control
Input volume slider with an auto preamp toggle that automatically reduces overall gain when boosting frequencies to prevent digital distortion.

### Balance and Stereo Width
Controls for mono audio, left/right channel swapping, balance positioning, and stereo width expansion.

### Headphone Filters
Optional filters designed for headphone listening:

- Loudness mode to restore bass and treble fullness at low volume levels.
- NVDA voice clarity to make screen reader speech cut through background audio.
- Vocal presence to highlight speech in calls and podcasts.
- Anti-fatigue filter for extended listening sessions (a fixed, constant treble cut — it doesn't adapt to the sound).
- Anti-sibilance filter to soften harsh treble sounds (a fixed, constant cut at that frequency — it doesn't detect individual "s" sounds).
- Deep bass boost for headphones lacking low-end punch.
- Subsonic filter to remove inaudible low-frequency rumble.
- Ground loop filter to eliminate 50/60 Hz electrical hum and its 100/120 Hz echoes.

### Tools and Diagnostics

- View Log button to inspect real-time audio commands.
- Conflict detection tool in the Tools menu to identify overlapping shortcuts.

---

## What's new in 1.4.0 (18 September 2026)

- Restored Equalizer APO download: resolved an internal issue in the setup helper that prevented downloading the official installer from the add-on menu.
- Preserved existing sound configurations: connecting Equalizer APO for the first time now preserves pre-existing settings from other devices or software, appending only the necessary include directive rather than overwriting the master configuration file.
- Automatic volume protection for built-in presets: selecting presets with strong frequency boosts (such as Bass Boost) now engages automatic preamplification proactively to prevent audio distortion in headphones.
- Smoother slider interaction: improved responsiveness when adjusting equalizer sliders rapidly, eliminating UI delays while audio commands are applied.
- Accurate profile cycling via shortcut: cycling through saved presets with keyboard shortcuts now reliably applies the exact profile announced by voice and shown in the dialog.
- Enhanced mains hum filtering: expanded electrical noise reduction to target 100 Hz and 120 Hz harmonic overtones in addition to the fundamental frequency.
- Clarified voice filter behavior: updated descriptions for anti-sibilance and anti-fatigue filters to reflect their fixed band attenuation characteristics.
- Updated installer package: the built-in installer download now points to current Equalizer APO version 1.4.2.
- Verified audio command pipeline: comprehensive verification of 31-band controls, balance, mono, tone, and filter commands against Equalizer APO specifications.

## What's new in 1.3.1 (13 September 2026)

- Lighter add-on footprint: removed unused internal dependencies across 5 modules, reducing the amount of code loaded by NVDA at startup.
- Complete internal technical documentation of all settings window controls, the download dialog, sound profiles, and the test tone generator.

## What's new in 1.3.0 (13 September 2026)

- Fixed stereo width expansion: previously, setting stereo width above 100% caused sound cancellation, leaving audio playing only through the right earphone. The stereo image now expands smoothly and evenly across both channels without volume loss.
- Smarter automatic volume protection: when combining multiple equalizer boosts and filters, the add-on accurately calculates overall gain to prevent distortion and protect your hearing and speakers.
- Preserved equalizer settings during quick adjustments: adjusting bass or treble with quick keys no longer resets your other equalizer sliders.
- Safe profile saving: profiles and settings are saved reliably, protecting your presets against corruption in case of sudden computer shutdowns.
- Automatic profile recovery: if a saved profile is damaged or incomplete, the add-on automatically restores safe defaults so your sound never cuts out.
- Resilient audio engine downloader: downloading Equalizer APO from the menu now uses chunked progress tracking and safely recovers from momentary internet interruptions.
- Smoother headphone orientation test: left, right, and center test tones now play smoothly with gentle fades, eliminating clicks and avoiding default Windows notification sounds when audio devices are busy.
- Improved settings window stability: resolved errors that could occur when quickly closing the settings dialog while audio adjustments were being applied.
- Clean uninstallation: uninstalling or updating the add-on completely removes temporary files without leaving leftover traces on your computer.

### Credits
- Audio Processing Engine: Equalizer APO by jthedering and contributors (GNU GPL).
- NVDA Add-on: Developed by Daliana.
