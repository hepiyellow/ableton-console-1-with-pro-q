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
# Format: Pro-Q 3 parameter name -> {'cc': Console 1 hardware control, 'invert': True/False}

# Combined parameter dictionary
PARAMETER_CC_MAP = {
    # Band 1 is now High Pass
    "Band 1 Frequency": {'cc': KNOB_HIGH_PASS, 'invert': False},
    
    # Frequency parameters (now bands 2-5)
    "Band 2 Frequency": {'cc': KNOB_EQ1_FREQ, 'invert': False},
    "Band 3 Frequency": {'cc': KNOB_EQ2_FREQ, 'invert': False},
    "Band 4 Frequency": {'cc': KNOB_EQ3_FREQ, 'invert': False},
    "Band 5 Frequency": {'cc': KNOB_EQ4_FREQ, 'invert': False},
    
    # Band 6 is now Low Pass
    "Band 6 Frequency": {'cc': KNOB_LOW_PASS, 'invert': False},
    
    # Gain parameters (now bands 2-5)
    "Band 2 Gain": {'cc': KNOB_EQ1_GAIN, 'invert': False},
    "Band 3 Gain": {'cc': KNOB_EQ2_GAIN, 'invert': False},
    "Band 4 Gain": {'cc': KNOB_EQ3_GAIN, 'invert': False},
    "Band 5 Gain": {'cc': KNOB_EQ4_GAIN, 'invert': False},
    
    # Shape parameters
    "Band 2 Shape": {'cc': BUTTON_EQ1_SHAPE, 'invert': False},
    "Band 5 Shape": {'cc': BUTTON_EQ4_SHAPE, 'invert': False},
    
    # Q parameters - corrected according to how hardware maps to Pro-Q bands
    "Band 3 Q": {'cc': BUTTON_EQ2_Q, 'invert': False},  # CC 90 - Hardware Band 2 maps to Pro-Q Band 3
    "Band 4 Q": {'cc': BUTTON_EQ3_Q, 'invert': False},  # CC 87 - Hardware Band 3 maps to Pro-Q Band 4
    
    # Add other Q parameters with appropriate mappings
    "Band 2 Q": {'cc': KNOB_EQ1_Q, 'invert': False},  # CC 94 - Using knob for Band 2 Q
    "Band 5 Q": {'cc': KNOB_EQ4_Q, 'invert': False},  # CC 84 - Using knob for Band 5 Q
    
    # Global parameters
    "Output Level": {'cc': KNOB_GAIN, 'invert': False},
    
    # Device control
    "Device On": {'cc': DISPLAY_ON, 'invert': False},  # EQ Bypass button controls Pro-Q3 Device On
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
CC_PARAMETER_MAP = {config['cc']: param for param, config in PARAMETER_CC_MAP.items()}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 