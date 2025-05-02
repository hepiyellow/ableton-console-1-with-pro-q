# Pro-Q 3 MIDI Mapping Configuration
# --------------------------------
# This file contains all MIDI mappings for the Pro-Q 3 controller script

# Import Console 1 hardware definitions
from .Console1_Hardware import *

# MIDI channel configuration (use the one from hardware definitions)
MIDI_CHANNEL = CONSOLE1_MIDI_CHANNEL

# Pro-Q 3 Parameter Mappings
# --------------------------
# Map Pro-Q 3 parameters to Console 1 knobs
# Format: Pro-Q 3 parameter name -> Console 1 hardware control

# Combined parameter dictionary
PARAMETER_CC_MAP = {
    # Band 1 is now High Pass
    "Band 1 Frequency": KNOB_HIGH_PASS,
    
    # Frequency parameters (now bands 2-5)
    "Band 2 Frequency": KNOB_EQ1_FREQ,
    "Band 3 Frequency": KNOB_EQ2_FREQ,
    "Band 4 Frequency": KNOB_EQ3_FREQ,
    "Band 5 Frequency": KNOB_EQ4_FREQ,
    
    # Band 6 is now Low Pass
    "Band 6 Frequency": KNOB_LOW_PASS,
    
    # Gain parameters (now bands 2-5)
    "Band 2 Gain": KNOB_EQ1_GAIN,
    "Band 3 Gain": KNOB_EQ2_GAIN,
    "Band 4 Gain": KNOB_EQ3_GAIN,
    "Band 5 Gain": KNOB_EQ4_GAIN,
    
    # Shape parameters
    "Band 2 Shape": BUTTON_EQ1_SHAPE,
    "Band 5 Shape": BUTTON_EQ4_SHAPE,
    
    # Q parameters - corrected according to how hardware maps to Pro-Q bands
    "Band 3 Q": BUTTON_EQ2_Q,  # CC 90 - Hardware Band 2 maps to Pro-Q Band 3
    "Band 4 Q": BUTTON_EQ3_Q,  # CC 87 - Hardware Band 3 maps to Pro-Q Band 4
    
    # Add other Q parameters with appropriate mappings
    "Band 2 Q": KNOB_EQ1_Q,  # CC 94 - Using knob for Band 2 Q
    "Band 5 Q": KNOB_EQ4_Q,  # CC 84 - Using knob for Band 5 Q
    
    # Global parameters
    "Output Level": KNOB_GAIN,
    
    # Device control
    "Device On": BUTTON_EQ_BYPASS,  # EQ Bypass button controls Pro-Q3 Device On
}

# Note about hardware controls and mappings:
# Hardware to Pro-Q mapping:
# - Hardware Band 2 Q button (CC 90) maps to Pro-Q Band 3 Q
# - Hardware Band 3 Q button (CC 87) maps to Pro-Q Band 4 Q
# - Hardware Band 1 Q knob (CC 94) maps to Pro-Q Band 2 Q
# - Hardware Band 4 Q knob (CC 84) maps to Pro-Q Band 5 Q
#
# This maintains the original hardware layout while allowing continuous Q control

# Create a reverse mapping for debugging/display purposes
# Maps CC numbers to parameter names
CC_PARAMETER_MAP = {cc: param for param, cc in PARAMETER_CC_MAP.items()}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 