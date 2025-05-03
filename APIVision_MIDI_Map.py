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
# Format: API Vision parameter name -> Console 1 hardware control

# Combined parameter dictionary
PARAMETER_CC_MAP = {
    # Filters
    "215 HP Filter": KNOB_HIGH_PASS,
    "215 LP Filter": KNOB_LOW_PASS,
    "215 On": BUTTON_FILTERS_TO_COMPRESSOR,
    # EQ Section
    "550 LF Freq": KNOB_EQ1_FREQ,  # Low frequency control
    "550 LF Gain": KNOB_EQ1_GAIN,  # Low gain control
    "550 LMF Freq": KNOB_EQ2_FREQ,  # Mid frequency control
    "550 LMF Gain": KNOB_EQ2_GAIN,  # Mid gain control
    "550 HMF Freq": KNOB_EQ3_FREQ,  # High frequency control
    "550 HMF Gain": KNOB_EQ3_GAIN,  # High gain control
    "550 HF Freq": KNOB_EQ4_FREQ,  # High frequency control
    "550 HF Gain": KNOB_EQ4_GAIN,  # High gain control
    
    "EQ On": BUTTON_EQ_BYPASS,

    "Line Gain": KNOB_SHAPE_SUSTAIN,
    "Mic Gain": KNOB_SHAPE_RELEASE,
    "Input Select": BUTTON_SHAPE_HARD_GATE,
    "Level": KNOB_SHAPE_PUNCH,
    # Compressor Section
    # "Threshold": KNOB_EQ4_FREQ,  # Compressor threshold
    # "Ratio": KNOB_EQ4_GAIN,  # Compressor ratio
    # "Attack": BUTTON_EQ1_SHAPE,  # Attack time
    # "Release": BUTTON_EQ4_SHAPE,  # Release time
    
    # Global controls
    # "Output Gain": KNOB_GAIN,  # Output level
    
    # These are stub mappings - update with actual parameter names after exploring the device
    # "Device On": BUTTON_EQ_BYPASS,  # Device bypass control
}

# Create a reverse mapping for debugging/display purposes
# Maps CC numbers to parameter names
CC_PARAMETER_MAP = {cc: param for param, cc in PARAMETER_CC_MAP.items()}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 