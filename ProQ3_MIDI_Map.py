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
    # Frequency parameters
    "Band 1 Frequency": KNOB_EQ1_FREQ,
    "Band 2 Frequency": KNOB_EQ2_FREQ,
    "Band 3 Frequency": KNOB_EQ3_FREQ,
    "Band 4 Frequency": KNOB_EQ4_FREQ,
    
    # Gain parameters
    "Band 1 Gain": KNOB_EQ1_GAIN,
    "Band 2 Gain": KNOB_EQ2_GAIN,
    "Band 3 Gain": KNOB_EQ3_GAIN,
    "Band 4 Gain": KNOB_EQ4_GAIN,
    
    # Additional parameters that could be mapped
    # Uncomment to enable these mappings
    # "Band 1 Q": KNOB_EQ1_Q,
    # "Band 2 Q": KNOB_EQ2_Q,
    # "Band 3 Q": KNOB_EQ3_Q,
    # "Band 4 Q": KNOB_EQ4_Q,
}

# Create a reverse mapping for debugging/display purposes
# Maps CC numbers to parameter names
CC_PARAMETER_MAP = {cc: param for param, cc in PARAMETER_CC_MAP.items()}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 