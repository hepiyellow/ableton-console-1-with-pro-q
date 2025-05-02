# Console1Control

A MIDI remote script for Ableton Live that allows a Console-1 hardware controller to control Pro-Q 3 EQ parameters and track functions.

## Description

This script enables comprehensive control over Pro-Q 3 parameters and track functions in Ableton Live using the Softube Console 1 hardware controller. It provides parameter mapping for frequency bands, gain, shape, and Q parameters, while also supporting track controls like volume, solo, and mute.

**Note: This entire script was AI-generated.**

**Warning: This script is currently in development and has not been extensively tested. Use at your own risk.**

## Requirements

### Pro-Q 3 Configuration

To use this script, you need to:

1. Create an Audio Effect Rack with FabFilter Pro-Q 3 inside it
2. Configure Pro-Q 3 with 6 bands including:
   - Band 1: High Pass filter
   - Bands 2-5: Regular EQ bands with frequency, gain, shape and Q parameters
   - Band 6: Low Pass filter

### Quick Setup Option

For a faster setup, you can use the pre-configured Rack device:

- [Console-1 With Pro-Q 3.adg](Console-1%20With%20Pro-Q%203.adg)

Just drag this device into your Ableton Live set and place it on any track you want to control.

## Features

- Controls Pro-Q 3 EQ parameters (frequency, gain, shape, and Q)
- Supports track volume, solo and mute functions
- Provides appropriate feedback to the controller
- Automatically finds Pro-Q 3 devices on any track
- Detects when Pro-Q 3 is added or removed
- Handles devices inside rack devices

## Installation

1. Place the entire folder in your Ableton Live Remote Scripts directory:

   - macOS: `~/Music/Ableton/User Library/Remote Scripts/`
   - Windows: `\Users\[username]\Documents\Ableton\User Library\Remote Scripts\`

2. Start Ableton Live
3. Go to Preferences > Link MIDI
4. Select "Console1Control" from the Control Surface dropdown menu
5. Set the Input to your Console 1 hardware controller
6. Set the Output to your Console 1 hardware controller
7. Make sure that Track and Remote are enabled for both Input and Output

After installation, add Pro-Q 3 to your desired track (preferably in a Rack as described in the Requirements section) and the script will automatically detect and connect to it. If you change tracks, the script will automatically reconnect to Pro-Q 3 if it exists on the new track.

## Files

- `Console1Controller.py` - Main controller class
- `Console1_Hardware.py` - Hardware definitions and MIDI mappings
- `ProQ3_MIDI_Map.py` - Pro-Q 3 parameter mappings
- `TrackControls_MIDI_Map.py` - Track control mappings
- `__init__.py` - Script initialization

## Usage

### Pro-Q 3 Controls

The Console 1 hardware controller maps to Pro-Q 3 parameters as follows:

- **Volume Knob**: Controls track volume
- **High-Pass Knob**: Controls Band 1 frequency (High Pass filter)
- **Low-Pass Knob**: Controls Band 6 frequency (Low Pass filter)
- **Gain Knob**: Controls Pro-Q 3 Output Level

For EQ Bands 2-5:

- **Frequency Knobs**: Control the frequency of each band
- **Gain Knobs**: Control the gain of each band
- **Shape Buttons**: Toggle between Shelf, Bell, and Cut modes
  - Band 2: Low Shelf, Bell, Low Cut
  - Band 5: High Shelf, Bell, High Cut
- **Q Buttons**: Cycle between Wide, Medium, and Narrow Q settings
  - For Bands 3 and 4

### Track Controls

- **Solo Button**: Toggles track solo
- **Mute Button**: Toggles track mute
- **Bypass Button**: Toggles Pro-Q 3 bypass

## License

MIT
