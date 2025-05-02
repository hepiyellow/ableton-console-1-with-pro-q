from __future__ import with_statement

import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement


class Console1Controller(ControlSurface):
    __doc__ = " Console1Controller script that controls Pro-Q 3 Band 1 Frequency with CC 92 "

    _active_instances = []

    def _combine_active_instances():
        pass
    _combine_active_instances = staticmethod(_combine_active_instances)

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("Console1Controller: Loaded successfully!")
        
        # Store Pro-Q 3 device and parameter references
        self._proq3_device = None
        self._band1_freq_param = None
        self._has_track_listener = False
        self._sending_feedback = False  # Flag to prevent feedback loops
        self._has_param_listener = False  # Track if parameter listener is connected
        
        with self.component_guard():
            # Define the MIDI channel to listen on (0-15)
            self._midi_channel = 0
            
            # Create a slider element for CC 92 (encoder with absolute values)
            self._cc92_encoder = SliderElement(MIDI_CC_TYPE, self._midi_channel, 92)
            
            # Add a value listener to the encoder
            self._cc92_encoder.add_value_listener(self._on_cc92_value)
            
            # Keep track of the last value to detect changes
            self._last_cc92_value = -1
            
            # Safely add track change listener
            self._setup_track_listener()
            
            self.log_message("Console1Controller: Listening for CC 92 encoder on channel", self._midi_channel + 1)

    def _setup_track_listener(self):
        """Setup the track selection listener safely"""
        try:
            # First try to remove the listener if it exists
            if self._has_track_listener:
                self.song().view.remove_selected_track_listener(self._on_selected_track_changed)
                self._has_track_listener = False
                self.log_message("Removed existing track listener")
                
            # Now add the listener
            self.song().view.add_selected_track_listener(self._on_selected_track_changed)
            self._has_track_listener = True
            self.log_message("Added track listener")
            
            # Initial device setup
            self._on_selected_track_changed()
        except Exception as e:
            self.log_message("Error setting up track listener:", str(e))

    def _remove_parameter_listener(self):
        """Safely remove parameter listener if it exists"""
        try:
            if self._has_param_listener and self._band1_freq_param and hasattr(self._band1_freq_param, 'remove_value_listener'):
                self._band1_freq_param.remove_value_listener(self._on_param_value_changed)
                self._has_param_listener = False
                self.log_message("Removed parameter listener")
        except Exception as e:
            self.log_message("Error removing parameter listener:", str(e))

    def _on_selected_track_changed(self):
        """Called when the selected track changes in Live"""
        # Clean up existing parameter listener
        self._remove_parameter_listener()
        
        # Reset device and parameter references
        self._proq3_device = None
        self._band1_freq_param = None
        
        try:
            track = self.song().view.selected_track
            self.log_message("Selected track:", track.name)
            
            # Find Pro-Q 3 in selected track's devices
            for device in track.devices:
                if device.name == "Pro-Q 3":
                    self._proq3_device = device
                    self.log_message("Found Pro-Q 3 on track:", track.name)
                    
                    # Find Band 1 Frequency parameter
                    for param in device.parameters:
                        if param.name == "Band 1 Frequency":
                            self._band1_freq_param = param
                            current_value = param.value
                            self.log_message("Found Band 1 Frequency parameter, current value:", current_value)
                            
                            # Send feedback to controller with current parameter value
                            self._send_parameter_feedback(current_value)
                            
                            # Add value listener to the parameter to update when Live changes the value
                            if hasattr(param, 'add_value_listener'):
                                try:
                                    self.log_message("Adding value listener to parameter")
                                    param.add_value_listener(self._on_param_value_changed)
                                    self._has_param_listener = True
                                except Exception as e:
                                    self.log_message("Error adding parameter listener:", str(e))
                            
                            break
                    
                    if not self._band1_freq_param:
                        self.log_message("Could not find Band 1 Frequency parameter")
                    break
            
            if not self._proq3_device:
                self.log_message("Could not find Pro-Q 3 device on track:", track.name)
        except Exception as e:
            self.log_message("Error in track change handler:", str(e))

    def _on_param_value_changed(self):
        """Called when the parameter value changes in Live"""
        if self._band1_freq_param:
            current_value = self._band1_freq_param.value
            self.log_message("Parameter value changed in Live:", current_value)
            self._send_parameter_feedback(current_value)

    def _send_parameter_feedback(self, param_value):
        """Send feedback to the controller with the current parameter value"""
        if not self._cc92_encoder:
            return
            
        try:
            # Prevent feedback loops
            if self._sending_feedback:
                return
                
            self._sending_feedback = True
            
            # Convert parameter value (0.0-1.0) to MIDI value (0-127)
            midi_value = int(param_value * 127)
            self.log_message("Sending feedback to controller, MIDI value:", midi_value)
            
            # Send the value back to the controller
            self._cc92_encoder.send_value(midi_value)
            
            # Update last value to avoid ping-pong
            self._last_cc92_value = midi_value
            
            self._sending_feedback = False
        except Exception as e:
            self._sending_feedback = False
            self.log_message("Error sending feedback:", str(e))

    def _on_cc92_value(self, value):
        """Called when CC 92 encoder is turned"""
        # Skip if we're in the middle of sending feedback to avoid loops
        if self._sending_feedback:
            return
            
        # Calculate the change from the last value
        change = 0
        if self._last_cc92_value >= 0:
            change = value - self._last_cc92_value
        
        self._last_cc92_value = value
        
        self.log_message("Encoder CC 92 value:", value, "change:", change)
        
        # If we have found the Pro-Q 3 device and Band 1 Frequency parameter
        if self._proq3_device and self._band1_freq_param:
            # Scale the encoder value (0-127) to parameter range
            # Assuming parameter range is 0.0 to 1.0
            param_value = value / 127.0
            
            # Update the parameter
            self._band1_freq_param.value = param_value
            self.log_message("Setting Pro-Q 3 Band 1 Frequency to:", param_value)
        else:
            self.log_message("No Pro-Q 3 device or Band 1 Frequency parameter found on selected track")

    def disconnect(self):
        # Remove listeners
        if hasattr(self, '_cc92_encoder') and self._cc92_encoder:
            self._cc92_encoder.remove_value_listener(self._on_cc92_value)
        
        # Remove parameter value listener
        self._remove_parameter_listener()
        
        # Remove track change listener
        try:
            if self._has_track_listener:
                self.song().view.remove_selected_track_listener(self._on_selected_track_changed)
                self._has_track_listener = False
        except Exception as e:
            self.log_message("Error removing track listener:", str(e))
            
        ControlSurface.disconnect(self)