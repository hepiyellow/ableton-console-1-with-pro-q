# UADx API Vision Channel Strip MIDI Mapping Configuration
# --------------------------------
# This file contains all MIDI mappings for the UADx API Vision Channel Strip

# Import Console 1 hardware definitions
from .Console1_Hardware import *

# MIDI channel configuration (use the same as other devices)
MIDI_CHANNEL = CONSOLE1_MIDI_CHANNEL

# API Vision Parameter Mappings
# --------------------------
# Map API Vision parameters to Console 1 knobs
# Format: API Vision parameter name -> { 'cc': Console 1 hardware control, 'invert': True/False }

# Combined parameter dictionary
PARAMETER_CC_MAP = {
    # Filters
    "215 HP Filter": {'cc': KNOB_HIGH_PASS, 'invert': False},
    "215 LP Filter": {'cc': KNOB_LOW_PASS, 'invert': False},
    "215 On": {'cc': BUTTON_FILTERS_TO_COMPRESSOR, 'invert': False},
    # EQ Section - Frequencies are inverted
    "550 LF Freq": {'cc': KNOB_EQ1_FREQ, 'invert': True},  # Low frequency control - INVERTED
    "550 LF Gain": {'cc': KNOB_EQ1_GAIN, 'invert': False},  # Low gain control
    "550 LMF Freq": {'cc': KNOB_EQ2_FREQ, 'invert': True},  # Mid frequency control - INVERTED
    "550 LMF Gain": {'cc': KNOB_EQ2_GAIN, 'invert': False},  # Mid gain control
    "550 HMF Freq": {'cc': KNOB_EQ3_FREQ, 'invert': True},  # High frequency control - INVERTED
    "550 HMF Gain": {'cc': KNOB_EQ3_GAIN, 'invert': False},  # High gain control
    "550 HF Freq": {'cc': KNOB_EQ4_FREQ, 'invert': True},  # High frequency control - INVERTED
    "550 HF Gain": {'cc': KNOB_EQ4_GAIN, 'invert': False},  # High gain control
    
    "EQ On": {'cc': BUTTON_EQ_BYPASS, 'invert': False},

    "Line Gain": {'cc': KNOB_SHAPE_SUSTAIN, 'invert': False},
    "Mic Gain": {'cc': KNOB_SHAPE_RELEASE, 'invert': False},
    "Input Select": {'cc': BUTTON_SHAPE_HARD_GATE, 'invert': False},
    "Level": {'cc': KNOB_SHAPE_PUNCH, 'invert': False},
    
    # Global controls - Uncomment and add as needed
    # "Output Gain": {'cc': KNOB_GAIN, 'invert': False},  # Output level
    
    # Device control
    "Device On": {'cc': BUTTON_EQ_BYPASS, 'invert': False},  # Device bypass control
}

# Create a reverse mapping for debugging/display purposes
# Maps CC numbers to parameter names
CC_PARAMETER_MAP = {config['cc']: param for param, config in PARAMETER_CC_MAP.items()}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 