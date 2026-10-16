# Audio Equalizer for NVDA

- Author: Daliana
- Version: 1.6.4
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

### Channel Configuration and Surround

The dialog includes a channel configuration list (stereo, 5.1, 7.1, quadraphonic and smart downmixes to stereo) with center, subwoofer and rear level controls. On stereo equipment, the center and subwoofer levels act as voice and bass enhancement; the rear level needs multichannel content. Smart downmixes act on movies or games with multichannel sound.

## Safety and Recovery

- Profiles and the active state are validated before they are loaded. If a settings file is damaged, the add-on restores safe values instead of preventing NVDA from starting.
- When a built-in profile is customized, a dated backup of the override is kept before it is replaced.
- Channel orders: stereo width, mono, swap, 3D and radar are sent to the audio engine. On some USB headsets they may cut all audio; if that happens, leave width at 100.
- Equalizer APO downloads use a secure connection, timeout, retries, and downloaded-file checks. You can cancel the download from its dialog.
- Radar and 3D surround cannot be enabled together because they are alternative effects.
- If Equalizer APO needs permission to update its configuration, NVDA announces it instead of repeatedly failing silently.

---

## What's new in 1.6.4

- Channel configuration and surround: channel mode list with center, subwoofer and rear levels.
- Stereo width using the syntax understood by the audio engine.
- Profiles with width at normal value and honest reporting of channel effects.

## What's new in 1.6.3

- Focus-jump and menu auto-open prevention: unique 'Ecualizador de &Audio' mnemonic (A key) in the Tools menu, removing the E-letter collision and involuntary auto-expansion while navigating with the keyboard.
- nvda.ini reading fix: resolved internal dictionary-unpack failure when reading NVDA AggregatedSection at startup, ensuring faithful restore of saved state.
- Preventive submenu cleanup when reloading add-ons without restarting NVDA.

## What's new in 1.6.2

- Menu stability: fixed and hardened the Tools-menu submenu lifecycle, ensuring clean event unbinding and safe removal when restarting or reloading add-ons.
- Involuntary activation prevention: accessible help text and precise identifier handling to avoid focus jumps or accidental openings.

## What's new in 1.6.1

- Indestructible Equalizer State Persistence: Fixed an issue where the equalizer could turn off or reset to flat/default on NVDA restart or PC reboot.
- Dual-Layer Persistence Architecture: Synchronous write-through to `nvda.ini` via `config.conf.save()` coupled with an atomic JSON state backup file resistant to sudden crashes and `NVDA + Control + F3` restarts.
- Resilient Configuration Loading: Tolerant parsing of gains lists formatted as comma-separated strings by ConfigObj, preventing silent fallback to factory defaults.
- Apply Button Persistence: Clicking "Apply" in the settings dialog now immediately flushes and persists settings to disk.
- Startup Factory Overrides: Customized factory presets are automatically restored into memory upon NVDA launch.

## What's new in 1.6.0

- Windows 10 & 11 Compatibility Fixes: Fixed missing 'surround_3d' and 'radar_mode' profile attributes and keyword arguments that caused TypeErrors during initialization and profile cloning.
- Resilient Logging & Diagnostics: Hardened write_audit_log to accept dynamic/future arguments safely and report spatial improvements (Haas 3D surround and HRTF Radar mode) in the log.
- GUI Enhancement: Added 3D Surround Effect checkbox to the Equalizer configuration dialog and added assignable shortcuts for spatial enhancements in Input Gestures.
- Secure Equalizer APO Downloader: Enforced explicit verified SSL context with Python 3.12+ compatibility to prevent download certificate validation failures on Windows 11.
- Factory Overrides Resilience: Fixed UnboundLocalError when accessing globalVars in secure mode or headless test environments.
- Clean Uninstallation: Removed factory overrides JSON and temp files on uninstall.
- Automatic Custom Mode: Modifying acoustic/spatial controls now automatically shifts the profile selector to 'Custom' without losing modifications.

## What's new in 1.5.1

- Radar Mode (Positional Audio): A dedicated 360-degree crossfeed and treble magnifying EQ specifically designed to enhance footsteps and spatial awareness in competitive gaming.
- Unlocked Preamplifier: Automatic preamp can now be disabled, allowing up to +20 dB raw gain boost for quiet sources.
- Binaural Profile: A new 'Warm Tilt' preset optimized for relaxing sounds and ASMR.
- Cinema EQ overhaul: The Movies preset now uses a heavy V-shape curve to expand the soundstage and reduce center-channel compression.
- Crash-proof JSON configuration: Background configuration files now self-heal in case of corruption caused by power outages.

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

### Third-party credits

*   Equalizer APO (https://sourceforge.net/projects/equalizerapo) by jthedering and contributors, under GNU GPLv2.

### Credits
- Audio Processing Engine: Equalizer APO by jthedering and contributors (GNU GPL).
- NVDA Add-on: Developed by Daliana.
