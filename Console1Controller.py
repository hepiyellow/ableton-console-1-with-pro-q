from __future__ import with_statement

import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement


class Console1Controller(ControlSurface):
    __doc__ = " Console1Controller script that listens to MIDI CC 92 encoder with absolute values "

    _active_instances = []

    def _combine_active_instances():
        pass
    _combine_active_instances = staticmethod(_combine_active_instances)

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("Console1Controller: Loaded successfully!")
        
        with self.component_guard():
            # Define the MIDI channel to listen on (0-15)
            self._midi_channel = 0
            
            # Create a slider element for CC 92 (encoder with absolute values)
            self._cc92_encoder = SliderElement(MIDI_CC_TYPE, self._midi_channel, 92)
            
            # Add a value listener to the encoder
            self._cc92_encoder.add_value_listener(self._on_cc92_value)
            
            # Keep track of the last value to detect changes
            self._last_cc92_value = -1
            
            self.log_message("Console1Controller: Listening for CC 92 encoder on channel", self._midi_channel + 1)

    def _on_cc92_value(self, value):
        # This function is called whenever CC 92 value changes
        # Since this encoder sends absolute values, value will be 0-127
        
        # Calculate the change from the last value
        change = 0
        if self._last_cc92_value >= 0:
            change = value - self._last_cc92_value
        
        self._last_cc92_value = value
        
        self.log_message("Console1Controller: Encoder CC 92 absolute value:", value, "change:", change)
        
        # You can add your custom functionality here based on the value

    def disconnect(self):
        # Remove the value listener
        if hasattr(self, '_cc92_encoder') and self._cc92_encoder:
            self._cc92_encoder.remove_value_listener(self._on_cc92_value)
            
        ControlSurface.disconnect(self)