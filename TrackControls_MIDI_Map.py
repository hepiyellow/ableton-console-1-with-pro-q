# Track Controls MIDI Mapping
# --------------------------------
# This file contains all MIDI mappings for track controls

# Import Console 1 hardware definitions
from .Console1_Hardware import BUTTON_TRACK_SOLO, BUTTON_TRACK_MUTE, KNOB_VOLUME

# Track Controls Parameter Mappings
# --------------------------------
# Map track controls to Console 1 buttons
# Format: Track control name -> Console 1 hardware control

TRACK_CONTROL_MAP = {
    # Track volume control
    "Volume": KNOB_VOLUME,
    
    # Track control parameters
    "Track Solo": BUTTON_TRACK_SOLO,
    "Track Mute": BUTTON_TRACK_MUTE,
    
    # Add more track controls here as needed
    # Example:
    # "Track Arm": BUTTON_TRACK_ARM,
}

# Create a reverse mapping for debugging/display purposes
# Maps CC numbers to parameter names
TRACK_CC_MAP = {cc: param for param, cc in TRACK_CONTROL_MAP.items()}

# Additional track control settings can be added here
# Example:
# DEFAULT_TRACK_STATES = {
#     "Track Solo": False,
#     "Track Mute": False,
# } 