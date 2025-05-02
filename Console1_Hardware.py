# Console 1 Hardware Definitions
# ---------------------------
# This file contains the hardware definitions for Console 1 buttons and knobs

# MIDI Channel (0-15, where 0 = Channel 1)
CONSOLE1_MIDI_CHANNEL = 0

# Console 1 Knob Definitions
# --------------------------

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

# Filter Knobs
KNOB_LOW_PASS = 105  # Low Pass Filter (Band 6)
KNOB_HIGH_PASS = 103  # High Pass Filter (Band 1)

# Global Controls
KNOB_GAIN = 107  # Gain control
KNOB_VOLUME = 7      # Volume control

# Shape Button Definitions
# -----------------------
# Shape buttons for Bands 1 and 4 - toggle between Shelf (0), Bell (63), and Cut (127)
BUTTON_EQ1_SHAPE = 93  # Band 1 Shape (maps to Pro-Q3 Band 2 Shape)
BUTTON_EQ4_SHAPE = 65  # Band 4 Shape (maps to Pro-Q3 Band 5 Shape)

# Q Button Definitions
# -------------------
# Q control buttons for Bands 2 and 3
BUTTON_EQ2_Q = 90  # Band 2 Q (maps to Pro-Q3 Band 3 Q)
BUTTON_EQ3_Q = 87  # Band 3 Q (maps to Pro-Q3 Band 4 Q)

# Shape value definitions
SHAPE_SHELF = 0
SHAPE_BELL = 63
SHAPE_CUT = 127

# Human-readable names for each control
CONTROL_NAMES = {
    KNOB_EQ1_FREQ: "EQ Band 1 Frequency",
    KNOB_EQ2_FREQ: "EQ Band 2 Frequency",
    KNOB_EQ3_FREQ: "EQ Band 3 Frequency",
    KNOB_EQ4_FREQ: "EQ Band 4 Frequency",
    
    KNOB_EQ1_GAIN: "EQ Band 1 Gain",
    KNOB_EQ2_GAIN: "EQ Band 2 Gain",
    KNOB_EQ3_GAIN: "EQ Band 3 Gain",
    KNOB_EQ4_GAIN: "EQ Band 4 Gain",
    
    KNOB_LOW_PASS: "Low Pass Frequency",
    KNOB_HIGH_PASS: "High Pass Frequency",
    
    BUTTON_EQ1_SHAPE: "EQ Band 1 Shape",
    BUTTON_EQ4_SHAPE: "EQ Band 4 Shape",
    
    BUTTON_EQ2_Q: "EQ Band 2 Q",
    BUTTON_EQ3_Q: "EQ Band 3 Q",
    
    KNOB_GAIN: "Gain",
    KNOB_VOLUME: "Volume"
} 