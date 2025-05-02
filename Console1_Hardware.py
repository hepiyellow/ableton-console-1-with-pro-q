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
KNOB_GAIN_SCALE = 107  # Gain Scale control

# Human-readable names for each control
CONTROL_NAMES = {
    KNOB_EQ1_FREQ: "Band 2 Frequency",
    KNOB_EQ2_FREQ: "Band 3 Frequency",
    KNOB_EQ3_FREQ: "Band 4 Frequency",
    KNOB_EQ4_FREQ: "Band 5 Frequency",
    
    KNOB_EQ1_GAIN: "Band 2 Gain",
    KNOB_EQ2_GAIN: "Band 3 Gain",
    KNOB_EQ3_GAIN: "Band 4 Gain",
    KNOB_EQ4_GAIN: "Band 5 Gain",
    
    KNOB_LOW_PASS: "Band 6 Frequency (Low Pass)",
    KNOB_HIGH_PASS: "Band 1 Frequency (High Pass)",
    
    KNOB_GAIN_SCALE: "Gain Scale"
} 