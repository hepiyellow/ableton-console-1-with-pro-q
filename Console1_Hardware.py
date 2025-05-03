# Console 1 Hardware Definitions
# ---------------------------
# This file contains the hardware definitions for Console 1 buttons and knobs

# MIDI Channel (0-15, where 0 = Channel 1)
CONSOLE1_MIDI_CHANNEL = 0

# Console 1 Knob Definitions
# --------------------------

# GLOBAL 
DISPLAY_ON = 102
DISPLAY_MODE = 104

# Frequency Knobs
KNOB_EQ1_FREQ = 92  # Band 2 Frequency (previously Band 1)
KNOB_EQ2_FREQ = 89  # Band 3 Frequency (previously Band 2)
KNOB_EQ3_FREQ = 86  # Band 4 Frequency (previously Band 3)
KNOB_EQ4_FREQ = 83  # Band 5 Frequency (previously Band 4)

# Gain Knobs
KNOB_EQ1_GAIN = 91  # Band 2 Gain (previously Band 1)
KNOB_EQ2_GAIN = 88  # Band 3 Gain (previously Band 2)
KNOB_EQ3_GAIN = 85  # Band 4 Gain (previously Band 3)
KNOB_EQ4_GAIN = 82  # Band 5 Gain (previously Band 4)

# Q Knobs
KNOB_EQ1_Q = 94  # Band 2 Q (previously Band 1) - CC 94
KNOB_EQ2_Q = 64  # Band 3 Q - suggested mapping - CC 64
KNOB_EQ3_Q = 66  # Band 4 Q - suggested mapping - CC 66
KNOB_EQ4_Q = 84  # Band 5 Q (previously Band 4) - CC 84

# Filter Knobs
KNOB_LOW_PASS = 105  # Low Pass Filter (Band 6)
KNOB_HIGH_PASS = 103  # High Pass Filter (Band 1)

# Shape Section
KNOB_SHAPE_RELEASE = 56
KNOB_SHAPE_SUSTAIN = 55
KNOB_SHAPE_PUNCH = 57
KNOB_SHAPE_GATE = 54
BUTTON_SHAPE_HARD_GATE = 59
BUTTON_SHAPE_BYPASS = 53

# Global Controls
KNOB_GAIN = 107  # Gain control
KNOB_VOLUME = 7      # Volume control
BUTTON_FILTERS_TO_COMPRESSOR = 61
BUTTON_PHASE_INV = 108
BUTTON_PRESET = 58


# Shape Button Definitions
# -----------------------
# Shape buttons for Bands 1 and 4 - toggle between Shelf (0), Bell (63), and Cut (127)
BUTTON_EQ1_SHAPE = 93  # Band 1 Shape (maps to Pro-Q3 Band 2 Shape)
BUTTON_EQ4_SHAPE = 65  # Band 4 Shape (maps to Pro-Q3 Band 5 Shape)

# Q Button Definitions
# -------------------
# Q control buttons for Bands 2 and 3
BUTTON_EQ2_Q = 90  # Band 2 Q (maps to Pro-Q3 Band 3 Q) - CC 90
BUTTON_EQ3_Q = 87  # Band 3 Q (maps to Pro-Q3 Band 4 Q) - CC 87

# Bypass Button Definition
# ----------------------
BUTTON_EQ_BYPASS = 80  # EQ Bypass button (maps to Pro-Q3 Device On)

# Track Control Buttons
# --------------------
BUTTON_TRACK_SOLO = 13  # Track Solo button
BUTTON_TRACK_MUTE = 12  # Track Mute button

# Shape value definitions
SHAPE_SHELF = 0
SHAPE_BELL = 63
SHAPE_CUT = 127

# Compressor
BUTTON_COMPRESSOR_BYPASS = 46
KNOB_COMPRESSOR_ATTACK = 51
KNOB_COMPRESSOR_RELEASE = 48
KNOB_COMPRESSOR_THRESHOLD = 47
KNOB_COMPRESSOR_RATIO = 49
KNOB_COMPRESSOR_PARALLEL = 50

# Human-readable names for each control
CONTROL_NAMES = {
    # GLobal
    DISPLAY_ON: "Display On",
    DISPLAY_MODE: "Display Mode",
    
    # Gain Section
    KNOB_GAIN: "Gain",
    BUTTON_FILTERS_TO_COMPRESSOR: "Filters to Compressor",
    BUTTON_PHASE_INV: "Phase Invert",
    BUTTON_PRESET: "Preset",

    KNOB_LOW_PASS: "Low Pass Frequency",
    KNOB_HIGH_PASS: "High Pass Frequency",
    
    # Shape Section
    KNOB_SHAPE_RELEASE: "Release",
    KNOB_SHAPE_SUSTAIN: "Sustain",
    KNOB_SHAPE_PUNCH: "Punch",
    KNOB_SHAPE_GATE: "Gate",
    BUTTON_SHAPE_HARD_GATE: "Hard Gate",
    BUTTON_SHAPE_BYPASS: "Shape Bypass",

    # EQ Section
    KNOB_EQ1_FREQ: "EQ Band 1 Frequency",
    KNOB_EQ2_FREQ: "EQ Band 2 Frequency",
    KNOB_EQ3_FREQ: "EQ Band 3 Frequency",
    KNOB_EQ4_FREQ: "EQ Band 4 Frequency",
    
    KNOB_EQ1_GAIN: "EQ Band 1 Gain",
    KNOB_EQ2_GAIN: "EQ Band 2 Gain",
    KNOB_EQ3_GAIN: "EQ Band 3 Gain",
    KNOB_EQ4_GAIN: "EQ Band 4 Gain",
    
    KNOB_EQ1_Q: "EQ Band 1 Q",
    KNOB_EQ2_Q: "EQ Band 2 Q",
    KNOB_EQ3_Q: "EQ Band 3 Q",
    KNOB_EQ4_Q: "EQ Band 4 Q",
    
    
    BUTTON_EQ1_SHAPE: "EQ Band 1 Shape",
    BUTTON_EQ4_SHAPE: "EQ Band 4 Shape",
    
    BUTTON_EQ2_Q: "EQ Band 2 Q",
    BUTTON_EQ3_Q: "EQ Band 3 Q",
    
    BUTTON_EQ_BYPASS: "EQ Bypass",

    #Compressor
    BUTTON_COMPRESSOR_BYPASS: "Compressor Bypass",
    KNOB_COMPRESSOR_THRESHOLD: "Compressor Threshold",
    KNOB_COMPRESSOR_RATIO: "Compressor Ratio",
    KNOB_COMPRESSOR_ATTACK: "Compressor Attack",
    KNOB_COMPRESSOR_RELEASE: "Compressor Release",
    KNOB_COMPRESSOR_PARALLEL: "Compressor Gain",
    
    # Track Control
    BUTTON_TRACK_SOLO: "Track Solo",
    BUTTON_TRACK_MUTE: "Track Mute",
    
    KNOB_VOLUME: "Volume"
} 