# Pro-Q 3 MIDI Mapping Configuration
# --------------------------------
# This file contains all MIDI mappings for the Pro-Q 3 controller script

# MIDI channel configuration (0-15, where 0 = Channel 1)
MIDI_CHANNEL = 0

# Control Change (CC) number mappings for Pro-Q 3 parameters
# Format: Parameter name -> CC number

# Frequency parameter mappings
BAND_1_FREQUENCY_CC = 92
BAND_2_FREQUENCY_CC = 89
BAND_3_FREQUENCY_CC = 86
BAND_4_FREQUENCY_CC = 83

# Gain parameter mappings
BAND_1_GAIN_CC = 91
BAND_2_GAIN_CC = 88
BAND_3_GAIN_CC = 85
BAND_4_GAIN_CC = 82

# Combined parameter dictionary
PARAMETER_CC_MAP = {
    # Frequency parameters
    "Band 1 Frequency": BAND_1_FREQUENCY_CC,
    "Band 2 Frequency": BAND_2_FREQUENCY_CC,
    "Band 3 Frequency": BAND_3_FREQUENCY_CC,
    "Band 4 Frequency": BAND_4_FREQUENCY_CC,
    
    # Gain parameters
    "Band 1 Gain": BAND_1_GAIN_CC,
    "Band 2 Gain": BAND_2_GAIN_CC,
    "Band 3 Gain": BAND_3_GAIN_CC,
    "Band 4 Gain": BAND_4_GAIN_CC,
}

# Logging settings
ENABLE_DEBUG_LOGGING = True  # Set to False to reduce log messages 