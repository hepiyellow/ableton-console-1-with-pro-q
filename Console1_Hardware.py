# Console 1 Hardware Definitions
# ---------------------------
# This file contains the hardware definitions for Console 1 buttons and knobs

# MIDI Channel (0-15, where 0 = Channel 1)
CONSOLE1_MIDI_CHANNEL = 0

# Console 1 Knob Definitions
# --------------------------

# Frequency Knobs
KNOB_EQ1_FREQ = 92  # Band 1 Frequency
KNOB_EQ2_FREQ = 89  # Band 2 Frequency
KNOB_EQ3_FREQ = 86  # Band 3 Frequency
KNOB_EQ4_FREQ = 83  # Band 4 Frequency

# Gain Knobs
KNOB_EQ1_GAIN = 91  # Band 1 Gain
KNOB_EQ2_GAIN = 88  # Band 2 Gain
KNOB_EQ3_GAIN = 85  # Band 3 Gain
KNOB_EQ4_GAIN = 82  # Band 4 Gain

# Human-readable names for each control
CONTROL_NAMES = {
    KNOB_EQ1_FREQ: "Band 1 Frequency",
    KNOB_EQ2_FREQ: "Band 2 Frequency",
    KNOB_EQ3_FREQ: "Band 3 Frequency",
    KNOB_EQ4_FREQ: "Band 4 Frequency",
    
    KNOB_EQ1_GAIN: "Band 1 Gain",
    KNOB_EQ2_GAIN: "Band 2 Gain",
    KNOB_EQ3_GAIN: "Band 3 Gain",
    KNOB_EQ4_GAIN: "Band 4 Gain"
} 