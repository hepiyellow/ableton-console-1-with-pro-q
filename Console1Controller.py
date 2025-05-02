from __future__ import with_statement

import Live
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement
from .ProQ3_MIDI_Map import PARAMETER_CC_MAP, MIDI_CHANNEL, ENABLE_DEBUG_LOGGING


class Console1Controller(ControlSurface):
    __doc__ = " Console1Controller script that controls Pro-Q 3 parameters with encoders "

    _active_instances = []
    
    # Mode settings
    EMULATE_RELATIVE_MODE = False  # False = absolute mode (0-127), True = relative mode (fixed steps)
    
    # Relative movement settings
    PARAMETER_STEP_SIZE = 0.01  # 1% change per encoder step
    FINE_STEP_SIZE = 0.001      # 0.1% change for fine control (not currently used)

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
        self._debug_logging = ENABLE_DEBUG_LOGGING
        
        # Get parameter CC map from the imported mapping file
        self._param_cc_map = PARAMETER_CC_MAP
        
        # Parameter references - will be populated when device is found
        self._param_refs = {}
        
        # Track reference - will be populated when track is found
        self._current_track = None
        
        # Encoder references - will be populated with actual SliderElements
        self._encoders = {}
        
        # Last MIDI values received for each encoder
        self._last_midi_values = {}
        
        # Current parameter percentage values (0.0-1.0)
        self._current_param_values = {}
        
        with self.component_guard():
            # Define the MIDI channel to listen on (from mapping file)
            self._midi_channel = MIDI_CHANNEL
            
            # Create encoders and set up listeners
            self._setup_encoders()
            
            # Safely add track change listener
            self._setup_track_listener()
            
            # Schedule the initial device setup to run after Live has fully loaded
            self.schedule_message(1, self._initial_device_setup)
            
            # Log the mode we're in
            mode_str = "relative (stepped)" if self.EMULATE_RELATIVE_MODE else "absolute (0-127)"
            self.log_message(f"Console1Controller: Encoder mode set to {mode_str}")
            self.log_message("Console1Controller: Setup complete, listening for encoder messages")
    
    def debug_log(self, *message):
        """Log message only if debug logging is enabled"""
        if self._debug_logging:
            self.log_message(*message)
    
    def _setup_encoders(self):
        """Create encoder elements and set up listeners"""
        for param_name, cc_number in self._param_cc_map.items():
            # Create a slider element for this CC number
            encoder = SliderElement(MIDI_CC_TYPE, self._midi_channel, cc_number)
            
            # Store the encoder in our dictionary
            self._encoders[param_name] = encoder
            
            # Initialize last values
            self._last_midi_values[param_name] = -1
            self._current_param_values[param_name] = 0.0
            
            # Add value listener with a closure to capture the parameter name
            def create_listener(param_name=param_name):
                def listener(value):
                    self._on_encoder_value(param_name, value)
                return listener
            
            # Add the value listener
            encoder.add_value_listener(create_listener())
            
            self.debug_log(f"Set up encoder for {param_name} on CC {cc_number}")

    def _initial_device_setup(self):
        """Initialize device and parameter setup on script load"""
        self.debug_log("Running initial device setup")
        
        # First check the currently selected track
        self._on_selected_track_changed()
        
        # If we didn't find the device on the selected track, search all tracks
        if not self._proq3_device:
            self.debug_log("Pro-Q 3 not found on selected track, searching all tracks")
            self._find_proq3_on_any_track()

    def _find_proq3_on_any_track(self):
        """Search all tracks for Pro-Q 3 device"""
        try:
            # Look through all tracks in the session
            for track_index, track in enumerate(self.song().tracks):
                self.debug_log("Checking track:", track.name)
                
                # Find Pro-Q 3 in track's devices
                for device in track.devices:
                    if device.name == "Pro-Q 3":
                        self._proq3_device = device
                        self._current_track = track
                        self.log_message("Found Pro-Q 3 on track:", track.name)
                        
                        # Find parameters and set up listeners
                        self._setup_proq3_parameters(device)
                        
                        # Select this track to make it visible to the user
                        self.song().view.selected_track = track
                        
                        return True
                
            # Also search return tracks
            for track in self.song().return_tracks:
                self.debug_log("Checking return track:", track.name)
                
                # Find Pro-Q 3 in track's devices
                for device in track.devices:
                    if device.name == "Pro-Q 3":
                        self._proq3_device = device
                        self._current_track = track
                        self.log_message("Found Pro-Q 3 on return track:", track.name)
                        
                        # Find parameters and set up listeners
                        self._setup_proq3_parameters(device)
                        
                        # Select this track to make it visible to the user
                        self.song().view.selected_track = track
                        
                        return True
            
            # Check master track
            master_track = self.song().master_track
            self.debug_log("Checking master track")
            
            # Find Pro-Q 3 in master track's devices
            for device in master_track.devices:
                if device.name == "Pro-Q 3":
                    self._proq3_device = device
                    self._current_track = master_track
                    self.log_message("Found Pro-Q 3 on master track")
                    
                    # Find parameters and set up listeners
                    self._setup_proq3_parameters(device)
                    
                    # Select master track to make it visible to the user
                    self.song().view.selected_track = master_track
                    
                    return True
            
            self.log_message("Could not find Pro-Q 3 device on any track")
            return False
            
        except Exception as e:
            self.log_message("Error in global device search:", str(e))
            return False

    def _setup_proq3_parameters(self, device):
        """Find all ProQ3 parameters needed and set up listeners"""
        try:
            self.debug_log("Setting up parameters for Pro-Q 3")
            
            # Find all ProQ3 parameters we need
            for param_name in self._param_cc_map.keys():
                # Skip Volume parameter as it's handled separately in _setup_track_volume
                if param_name == "Volume":
                    continue
                    
                for param in device.parameters:
                    if param.name == param_name:
                        self._param_refs[param_name] = param
                        current_value = param.value
                        self._current_param_values[param_name] = current_value
                        self.debug_log(f"Found {param_name} parameter, current value: {current_value}")
                        
                        # Send feedback to controller with current parameter value (silent)
                        if param_name in self._encoders:
                            self._send_parameter_feedback(param_name, current_value, silent=True)
                        
                        # Add value listener to the parameter to update when Live changes the value
                        self._setup_parameter_listener(param_name, param)
                        
                        break
                
                # Check if we found the parameter
                if param_name not in self._param_refs and param_name != "Volume":
                    self.debug_log(f"Could not find {param_name} parameter")
            
            # Log summary of found parameters
            found_proq3_params = sum(1 for name in self._param_refs if name != "Volume")
            total_proq3_params = len(self._param_cc_map) - (1 if "Volume" in self._param_cc_map else 0)
            self.log_message(f"Found {found_proq3_params} of {total_proq3_params} Pro-Q 3 parameters")
                
        except Exception as e:
            self.log_message("Error setting up Pro-Q 3 parameters:", str(e))

    def _setup_track_volume(self, track):
        """Set up volume parameter for the specified track"""
        try:
            if "Volume" in self._param_cc_map and track and track.mixer_device and hasattr(track.mixer_device, 'volume'):
                volume_param = track.mixer_device.volume
                self._param_refs["Volume"] = volume_param
                current_value = volume_param.value
                self._current_param_values["Volume"] = current_value
                self.debug_log(f"Found Volume parameter for track: {track.name}, current value: {current_value}")
                
                # Send feedback to controller with current parameter value (silent)
                if "Volume" in self._encoders:
                    self._send_parameter_feedback("Volume", current_value, silent=True)
                
                # Add value listener to the parameter to update when Live changes the value
                self._setup_parameter_listener("Volume", volume_param)
                
                return True
            return False
        except Exception as e:
            self.log_message("Error setting up track volume:", str(e))
            return False

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
                
                self.debug_log(f"Added value listener to {param_name}")
            except Exception as e:
                self.log_message(f"Error adding parameter listener to {param_name}:", str(e))

    def _setup_track_listener(self):
        """Setup the track selection listener safely"""
        try:
            # First try to remove the listener if it exists
            if self._has_track_listener:
                self.song().view.remove_selected_track_listener(self._on_selected_track_changed)
                self._has_track_listener = False
                self.debug_log("Removed existing track listener")
                
            # Now add the listener
            self.song().view.add_selected_track_listener(self._on_selected_track_changed)
            self._has_track_listener = True
            self.debug_log("Added track listener")
            
        except Exception as e:
            self.log_message("Error setting up track listener:", str(e))

    def _remove_parameter_listeners(self):
        """Safely remove all parameter listeners"""
        try:
            if hasattr(self, '_param_listeners'):
                for param_name, (param, listener) in self._param_listeners.items():
                    if param and hasattr(param, 'remove_value_listener'):
                        param.remove_value_listener(listener)
                        self.debug_log(f"Removed listener for {param_name}")
                
                self._param_listeners = {}
                self.debug_log("Removed all parameter listeners")
        except Exception as e:
            self.log_message("Error removing parameter listeners:", str(e))

    def _on_selected_track_changed(self):
        """Called when the selected track changes in Live"""
        # Clean up existing parameter listeners
        self._remove_parameter_listeners()
        
        # Reset device reference but keep Volume parameter separate
        self._proq3_device = None
        
        # Keep only the Volume parameter if it exists
        if "Volume" in self._param_refs:
            volume_param = self._param_refs["Volume"]
            self._param_refs = {"Volume": volume_param}
        else:
            self._param_refs = {}
        
        try:
            track = self.song().view.selected_track
            self._current_track = track
            self.debug_log("Selected track:", track.name)
            
            # Set up volume parameter for the new track
            self._setup_track_volume(track)
            
            # Find Pro-Q 3 in selected track's devices
            for device in track.devices:
                if device.name == "Pro-Q 3":
                    self._proq3_device = device
                    self.log_message("Found Pro-Q 3 on track:", track.name)
                    
                    # Find parameters and set up listeners
                    self._setup_proq3_parameters(device)
                    break
            
            if not self._proq3_device:
                self.debug_log("Could not find Pro-Q 3 device on track:", track.name)
                # Even with no ProQ3, we still have the Volume parameter set up above
                self.log_message(f"Track volume control active for: {track.name}")
        except Exception as e:
            self.log_message("Error in track change handler:", str(e))

    def _on_param_value_changed(self, param_name):
        """Called when a parameter value changes in Live"""
        if param_name in self._param_refs:
            # Skip if the change was triggered by our controller
            if self._parameter_value_changed_from_controller:
                self._parameter_value_changed_from_controller = False
                return
                
            # Get the current value and update our tracking
            current_value = self._param_refs[param_name].value
            self._current_param_values[param_name] = current_value
            
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
            
            # Log message only if not silent and debug logging is enabled
            if not silent and self._debug_logging:
                self.debug_log(f"Sending feedback for {param_name}, MIDI value: {midi_value}")
            
            # Send the value back to the controller
            self._encoders[param_name].send_value(midi_value)
            
            # Update last value to avoid ping-pong
            self._last_midi_values[param_name] = midi_value
            
            self._sending_feedback = False
        except Exception as e:
            self._sending_feedback = False
            self.log_message(f"Error sending feedback for {param_name}:", str(e))

    def _determine_relative_change(self, param_name, new_value):
        """Determine the relative change direction based on current and new MIDI values"""
        last_value = self._last_midi_values[param_name]
        
        # If we don't have a previous value, just store this one and return no change
        if last_value == -1:
            self._last_midi_values[param_name] = new_value
            return 0
        
        # Store the new value
        self._last_midi_values[param_name] = new_value
        
        # Determine direction of change
        if new_value > last_value:
            # Moving up
            return 1
        elif new_value < last_value:
            # Moving down
            return -1
        
        # Handle wraparound cases
        if new_value == 0 and last_value == 0:
            # Repeated zero usually means going down past zero
            return -1
        elif new_value == 127 and last_value == 127:
            # Repeated 127 usually means going up past 127
            return 1
            
        # No change detected
        return 0

    def _on_encoder_value(self, param_name, value):
        """Called when an encoder is turned, handling according to mode setting"""
        # Skip if we're in the middle of sending feedback to avoid loops
        if self._sending_feedback:
            return
        
        # Handle volume separately from Pro-Q 3 parameters
        if param_name == "Volume" and param_name in self._param_refs:
            self._handle_parameter_change(param_name, value)
            return
            
        # Handle Pro-Q 3 parameters only if device exists
        if self._proq3_device and param_name in self._param_refs:
            self._handle_parameter_change(param_name, value)
        else:
            self.debug_log(f"No Pro-Q 3 device or {param_name} parameter found")

    def _handle_parameter_change(self, param_name, value):
        """Handle parameter value changes from encoder movement"""
        # Set flag to indicate the parameter change came from our controller
        self._parameter_value_changed_from_controller = True
        
        # Get the parameter
        param = self._param_refs[param_name]
        
        if self.EMULATE_RELATIVE_MODE:
            # ------ RELATIVE MODE ------
            # Determine the direction of movement
            change_direction = self._determine_relative_change(param_name, value)
            
            # Skip if no change detected
            if change_direction == 0:
                return
            
            # Get current parameter value
            current_value = self._current_param_values[param_name]
            
            # Calculate the new value with the appropriate step size
            new_value = current_value + (change_direction * self.PARAMETER_STEP_SIZE)
            
            # Clamp to 0.0-1.0 range
            new_value = max(0.0, min(1.0, new_value))
            
            # Update our tracking value
            self._current_param_values[param_name] = new_value
            
            # Log the change if debug is enabled
            self.debug_log(f"Encoder {param_name} - Direction: {change_direction}, " + 
                          f"Old value: {current_value:.3f}, New value: {new_value:.3f}")
        else:
            # ------ ABSOLUTE MODE ------
            # Store the MIDI value
            self._last_midi_values[param_name] = value
            
            # Scale the encoder value (0-127) to parameter range (0.0-1.0)
            new_value = value / 127.0
            
            # Update our tracking value
            self._current_param_values[param_name] = new_value
            
            # Log the change if debug is enabled
            self.debug_log(f"Encoder {param_name} - Absolute value: {value}, Param value: {new_value:.3f}")
        
        # Update the parameter in Live
        param.value = new_value

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