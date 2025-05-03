# UADx Neve 1073 Preamp And EQ MIDI Mapping Configuration
# --------------------------------
# This file contains all MIDI mappings for the UADx Neve 1073 Preamp And EQ device

# Import Console 1 hardware definitions
from .Console1_Hardware import *

# MIDI channel configuration (use the same as other devices)
MIDI_CHANNEL = CONSOLE1_MIDI_CHANNEL

# Neve 1073 Parameter Mappings
# --------------------------
# Map Neve 1073 parameters to Console 1 knobs
# Format: Neve 1073 parameter name -> { 'cc': Console 1 hardware control, 'invert': True/False }

# Combined parameter dictionary
PARAMETER_CC_MAP = {
    # EQ Section
    # "High Freq": {'cc': KNOB_EQ4_FREQ, 'invert': True},  # High frequency control - INVERTED
    "HF Gain": {'cc': KNOB_EQ4_GAIN, 'invert': False},  # High gain control
    
    "MF Freq": {'cc': KNOB_EQ3_FREQ, 'invert': False},  # Mid frequency control - INVERTED
    "MF Gain": {'cc': KNOB_EQ3_GAIN, 'invert': False},  # Mid gain control
    
    "LF Freq": {'cc': KNOB_EQ2_FREQ, 'invert': False},  # Low frequency control - INVERTED
    "LF Gain": {'cc': KNOB_EQ2_GAIN, 'invert': False},  # Low gain control
    
    "High Pass": {'cc': KNOB_EQ1_GAIN, 'invert': False},  # High-pass filter
    
    # Input Section
    "Line Gain": {'cc': KNOB_GAIN, 'invert': False},  # Input gain control
    "Output": {'cc': KNOB_SHAPE_GATE, 'invert': False},  # Output trim
    "Level": {'cc': KNOB_SHAPE_PUNCH, 'invert': False},  # Output level control
    # Bypass control
    "Device On": {'cc': BUTTON_EQ_BYPASS, 'invert': False},  # Device bypass control
}

# Create a reverse mapping for debugging/display purposes
# Maps CC numbers to parameter names
CC_PARAMETER_MAP = {config['cc']: param for param, config in PARAMETER_CC_MAP.items()}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 