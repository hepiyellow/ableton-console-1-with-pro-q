from __future__ import with_statement

import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement


class Console1Controller(ControlSurface):
    __doc__ = " Console1Controller script that controls Pro-Q 3 parameters with encoders "

    _active_instances = []

    def _combine_active_instances():
        pass
    _combine_active_instances = staticmethod(_combine_active_instances)

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        self.log_message("Console1Controller: Loaded successfully!")
        
        # Store Pro-Q 3 device reference
        self._proq3_device = None
        self._has_track_listener = False
        self._sending_feedback = False  # Flag to prevent feedback loops
        self._has_param_listener = False  # Track if parameter listener is connected
        self._parameter_value_changed_from_controller = False  # Flag to track source of value changes
        
        # Encoder mappings - CC numbers for each parameter
        self._param_cc_map = {
            # Format: (parameter_name, cc_number)
            "Band 1 Frequency": 92,
            "Band 2 Frequency": 89,
            "Band 3 Frequency": 86,
            "Band 4 Frequency": 83,
            "Band 1 Gain": 91,
            "Band 2 Gain": 88,
            "Band 3 Gain": 85,
            "Band 4 Gain": 82
        }
        
        # Parameter references - will be populated when device is found
        self._param_refs = {}
        
        # Encoder references - will be populated with actual SliderElements
        self._encoders = {}
        
        # Last values for each encoder
        self._last_values = {}
        
        with self.component_guard():
            # Define the MIDI channel to listen on (0-15)
            self._midi_channel = 0
            
            # Create encoders and set up listeners
            self._setup_encoders()
            
            # Safely add track change listener
            self._setup_track_listener()
            
            # Schedule the initial device setup to run after Live has fully loaded
            self.schedule_message(1, self._initial_device_setup)
            
            self.log_message("Console1Controller: Setup complete, listening for encoder messages")
    
    def _setup_encoders(self):
        """Create encoder elements and set up listeners"""
        for param_name, cc_number in self._param_cc_map.items():
            # Create a slider element for this CC number
            encoder = SliderElement(MIDI_CC_TYPE, self._midi_channel, cc_number)
            
            # Store the encoder in our dictionary
            self._encoders[param_name] = encoder
            
            # Initialize last value
            self._last_values[param_name] = -1
            
            # Add value listener with a closure to capture the parameter name
            def create_listener(param_name=param_name):
                def listener(value):
                    self._on_encoder_value(param_name, value)
                return listener
            
            # Add the value listener
            encoder.add_value_listener(create_listener())
            
            self.log_message(f"Set up encoder for {param_name} on CC {cc_number}")

    def _initial_device_setup(self):
        """Initialize device and parameter setup on script load"""
        self.log_message("Running initial device setup")
        
        # First check the currently selected track
        self._on_selected_track_changed()
        
        # If we didn't find the device on the selected track, search all tracks
        if not self._proq3_device:
            self.log_message("Pro-Q 3 not found on selected track, searching all tracks")
            self._find_proq3_on_any_track()

    def _find_proq3_on_any_track(self):
        """Search all tracks for Pro-Q 3 device"""
        try:
            # Look through all tracks in the session
            for track_index, track in enumerate(self.song().tracks):
                self.log_message("Checking track:", track.name)
                
                # Find Pro-Q 3 in track's devices
                for device in track.devices:
                    if device.name == "Pro-Q 3":
                        self._proq3_device = device
                        self.log_message("Found Pro-Q 3 on track:", track.name)
                        
                        # Find parameters and set up listeners
                        self._setup_parameters_for_device(device)
                        
                        # Select this track to make it visible to the user
                        self.song().view.selected_track = track
                        
                        return True
                
            # Also search return tracks
            for track in self.song().return_tracks:
                self.log_message("Checking return track:", track.name)
                
                # Find Pro-Q 3 in track's devices
                for device in track.devices:
                    if device.name == "Pro-Q 3":
                        self._proq3_device = device
                        self.log_message("Found Pro-Q 3 on return track:", track.name)
                        
                        # Find parameters and set up listeners
                        self._setup_parameters_for_device(device)
                        
                        # Select this track to make it visible to the user
                        self.song().view.selected_track = track
                        
                        return True
            
            # Check master track
            master_track = self.song().master_track
            self.log_message("Checking master track")
            
            # Find Pro-Q 3 in master track's devices
            for device in master_track.devices:
                if device.name == "Pro-Q 3":
                    self._proq3_device = device
                    self.log_message("Found Pro-Q 3 on master track")
                    
                    # Find parameters and set up listeners
                    self._setup_parameters_for_device(device)
                    
                    # Select master track to make it visible to the user
                    self.song().view.selected_track = master_track
                    
                    return True
            
            self.log_message("Could not find Pro-Q 3 device on any track")
            return False
            
        except Exception as e:
            self.log_message("Error in global device search:", str(e))
            return False

    def _setup_parameters_for_device(self, device):
        """Find all needed parameters for the device and set up listeners"""
        self._param_refs = {}  # Reset parameter references
        
        # Clear all parameter listeners
        self._remove_parameter_listeners()
        
        try:
            self.log_message("Setting up parameters for Pro-Q 3")
            
            # Find all parameters we need
            for param_name in self._param_cc_map.keys():
                for param in device.parameters:
                    if param.name == param_name:
                        self._param_refs[param_name] = param
                        current_value = param.value
                        self.log_message(f"Found {param_name} parameter, current value: {current_value}")
                        
                        # Send feedback to controller with current parameter value (silent)
                        if param_name in self._encoders:
                            self._send_parameter_feedback(param_name, current_value, silent=True)
                        
                        # Add value listener to the parameter to update when Live changes the value
                        self._setup_parameter_listener(param_name, param)
                        
                        break
                
                # Check if we found the parameter
                if param_name not in self._param_refs:
                    self.log_message(f"Could not find {param_name} parameter")
            
            # Log summary of found parameters
            if self._param_refs:
                self.log_message(f"Found {len(self._param_refs)} of {len(self._param_cc_map)} parameters")
            else:
                self.log_message("Could not find any required parameters")
                
        except Exception as e:
            self.log_message("Error setting up parameters:", str(e))

    def _setup_parameter_listener(self, param_name, param):
        """Setup a listener for parameter value changes"""
        if hasattr(param, 'add_value_listener'):
            try:
                # Create a closure to capture the parameter name
                def create_listener(param_name=param_name):
                    def listener():
                        self._on_param_value_changed(param_name)
                    return listener
                
                # Add the listener
                listener = create_listener()
                param.add_value_listener(listener)
                
                # Store listener reference for later removal
                if '_param_listeners' not in dir(self):
                    self._param_listeners = {}
                self._param_listeners[param_name] = (param, listener)
                
                self.log_message(f"Added value listener to {param_name}")
            except Exception as e:
                self.log_message(f"Error adding parameter listener to {param_name}:", str(e))

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
            
        except Exception as e:
            self.log_message("Error setting up track listener:", str(e))

    def _remove_parameter_listeners(self):
        """Safely remove all parameter listeners"""
        try:
            if hasattr(self, '_param_listeners'):
                for param_name, (param, listener) in self._param_listeners.items():
                    if param and hasattr(param, 'remove_value_listener'):
                        param.remove_value_listener(listener)
                        self.log_message(f"Removed listener for {param_name}")
                
                self._param_listeners = {}
                self.log_message("Removed all parameter listeners")
        except Exception as e:
            self.log_message("Error removing parameter listeners:", str(e))

    def _on_selected_track_changed(self):
        """Called when the selected track changes in Live"""
        # Clean up existing parameter listeners
        self._remove_parameter_listeners()
        
        # Reset device and parameter references
        self._proq3_device = None
        self._param_refs = {}
        
        try:
            track = self.song().view.selected_track
            self.log_message("Selected track:", track.name)
            
            # Find Pro-Q 3 in selected track's devices
            for device in track.devices:
                if device.name == "Pro-Q 3":
                    self._proq3_device = device
                    self.log_message("Found Pro-Q 3 on track:", track.name)
                    
                    # Find parameters and set up listeners
                    self._setup_parameters_for_device(device)
                    break
            
            if not self._proq3_device:
                self.log_message("Could not find Pro-Q 3 device on track:", track.name)
        except Exception as e:
            self.log_message("Error in track change handler:", str(e))

    def _on_param_value_changed(self, param_name):
        """Called when a parameter value changes in Live"""
        if param_name in self._param_refs:
            # Skip if the change was triggered by our controller
            if self._parameter_value_changed_from_controller:
                self._parameter_value_changed_from_controller = False
                return
                
            # Get the current value
            current_value = self._param_refs[param_name].value
            
            # Send feedback to controller with the updated value
            self._send_parameter_feedback(param_name, current_value)

    def _send_parameter_feedback(self, param_name, param_value, silent=False):
        """Send feedback to the controller with the current parameter value"""
        if param_name not in self._encoders:
            return
            
        try:
            # Prevent feedback loops
            if self._sending_feedback:
                return
                
            self._sending_feedback = True
            
            # Convert parameter value (0.0-1.0) to MIDI value (0-127)
            midi_value = int(param_value * 127)
            
            # Log message only if not silent
            if not silent:
                self.log_message(f"Sending feedback for {param_name}, MIDI value: {midi_value}")
            
            # Send the value back to the controller
            self._encoders[param_name].send_value(midi_value)
            
            # Update last value to avoid ping-pong
            self._last_values[param_name] = midi_value
            
            self._sending_feedback = False
        except Exception as e:
            self._sending_feedback = False
            self.log_message(f"Error sending feedback for {param_name}:", str(e))

    def _on_encoder_value(self, param_name, value):
        """Called when an encoder is turned"""
        # Skip if we're in the middle of sending feedback to avoid loops
        if self._sending_feedback:
            return
            
        # If we have found the parameter
        if self._proq3_device and param_name in self._param_refs:
            # Set flag to indicate the parameter change came from our controller
            self._parameter_value_changed_from_controller = True
            
            # Get the parameter
            param = self._param_refs[param_name]
            
            # Calculate the change from the last value
            change = 0
            if self._last_values[param_name] >= 0:
                change = value - self._last_values[param_name]
            
            # Update last value
            self._last_values[param_name] = value
            
            # Scale the encoder value (0-127) to parameter range
            # Assuming parameter range is 0.0 to 1.0
            param_value = value / 127.0
            
            # Update the parameter
            param.value = param_value
        else:
            self.log_message(f"No Pro-Q 3 device or {param_name} parameter found")

    def disconnect(self):
        # Remove encoder listeners
        for param_name, encoder in self._encoders.items():
            if encoder:
                # Get all listeners and remove them - this is tricky with closures
                for slot_id, slot in encoder._value_slots.items():
                    if slot:
                        encoder.remove_value_listener(slot)
        
        # Remove parameter listeners
        self._remove_parameter_listeners()
        
        # Remove track change listener
        try:
            if self._has_track_listener:
                self.song().view.remove_selected_track_listener(self._on_selected_track_changed)
                self._has_track_listener = False
        except Exception as e:
            self.log_message("Error removing track listener:", str(e))
            
        ControlSurface.disconnect(self)