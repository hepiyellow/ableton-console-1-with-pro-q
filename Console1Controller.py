from __future__ import with_statement

import Live
import time
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement
from .ProQ3_MIDI_Map import PARAMETER_CC_MAP, MIDI_CHANNEL, ENABLE_DEBUG_LOGGING
from .Console1_Hardware import SHAPE_SHELF, SHAPE_BELL, SHAPE_CUT, BUTTON_EQ_BYPASS


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
            
            # Log shape mapping for debugging
            self.schedule_message(2, self._log_shape_mappings)
            
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

    def _find_proq3_in_device(self, device, track):
        """Recursively search for Pro-Q 3 within a device (for racks)"""
        # Check if this device is Pro-Q 3
        if device.name == "Pro-Q 3":
            self._proq3_device = device
            self._current_track = track
            self.log_message(f"Found Pro-Q 3 in rack on track: {track.name}")
            self._setup_proq3_parameters(device)
            return True
        
        # Check if this device is a rack with chains
        if hasattr(device, 'chains') and len(device.chains) > 0:
            # Look through all chains in the rack
            for chain in device.chains:
                # Look through all devices in the chain
                for chain_device in chain.devices:
                    # Recursive search in each device
                    if self._find_proq3_in_device(chain_device, track):
                        return True
        return False

    def _find_proq3_on_any_track(self):
        """Search all tracks for Pro-Q 3 device, including inside racks"""
        try:
            # Look through all tracks in the session
            for track_index, track in enumerate(self.song().tracks):
                self.debug_log("Checking track:", track.name)
                
                # Find Pro-Q 3 in track's devices (direct or in racks)
                for device in track.devices:
                    if self._find_proq3_in_device(device, track):
                        # Select this track to make it visible to the user
                        self.song().view.selected_track = track
                        return True
                
            # Also search return tracks
            for track in self.song().return_tracks:
                self.debug_log("Checking return track:", track.name)
                
                # Find Pro-Q 3 in track's devices (direct or in racks)
                for device in track.devices:
                    if self._find_proq3_in_device(device, track):
                        # Select this track to make it visible to the user
                        self.song().view.selected_track = track
                        return True
            
            # Check master track
            master_track = self.song().master_track
            self.debug_log("Checking master track")
            
            # Find Pro-Q 3 in master track's devices (direct or in racks)
            for device in master_track.devices:
                if self._find_proq3_in_device(device, master_track):
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
            
            # Find Pro-Q 3 in selected track's devices (direct or in racks)
            proq3_found = False
            
            # Check direct devices first
            for device in track.devices:
                if device.name == "Pro-Q 3":
                    self._proq3_device = device
                    self.log_message("Found Pro-Q 3 on track:", track.name)
                    
                    # Find parameters and set up listeners
                    self._setup_proq3_parameters(device)
                    proq3_found = True
                    break
            
            # If not found, check for racks
            if not proq3_found:
                for device in track.devices:
                    if hasattr(device, 'chains') and len(device.chains) > 0:
                        # This is a rack, search inside it
                        if self._find_proq3_in_device(device, track):
                            proq3_found = True
                            break
                            
            if not proq3_found:
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
            
            # Print raw parameter value for debugging
            # This is especially useful for Shape parameters to see their actual values
            param = self._param_refs[param_name]
            if hasattr(param, 'name'):
                if "Shape" in param.name:
                    raw_value = current_value
                    self.log_message(f"RAW PARAMETER VALUE: {param_name} = {raw_value}")
                    
                    # Determine which shape this value represents based on exact values
                    # Bell = 0.0 (for both Band 2 and 5)
                    # Low Shelf = 1.0 (for Band 2)
                    # Low Cut = 2.0 (for Band 2)
                    # High Shelf = 3.0 (for Band 5)
                    # High Cut = 4.0 (for Band 5)
                    
                    if abs(raw_value) < 0.1:  # Bell (value = 0.0)
                        shape_name = "BELL"
                    elif "Band 2" in param_name:
                        # Band 2 specific shapes
                        if abs(raw_value - 1.0) < 0.1:  # Low Shelf (value = 1.0)
                            shape_name = "LOW SHELF"
                        elif abs(raw_value - 2.0) < 0.1:  # Low Cut (value = 2.0)
                            shape_name = "LOW CUT"
                        else:
                            shape_name = f"UNKNOWN (value = {raw_value})"
                    elif "Band 5" in param_name:
                        # Band 5 specific shapes
                        if abs(raw_value - 3.0) < 0.1:  # High Shelf (value = 3.0)
                            shape_name = "HIGH SHELF"
                        elif abs(raw_value - 4.0) < 0.1:  # High Cut (value = 4.0)
                            shape_name = "HIGH CUT"
                        else:
                            shape_name = f"UNKNOWN (value = {raw_value})"
                    else:
                        shape_name = f"UNKNOWN (value = {raw_value})"
                    
                    self.log_message(f"SHAPE TYPE: {shape_name}")
                elif "Q" in param.name:
                    # Log Q parameter values for debugging
                    raw_value = current_value
                    self.log_message(f"RAW Q VALUE: {param_name} = {raw_value}")
                    
                    # Determine approximate Q setting
                    if raw_value >= 0.8:
                        q_type = "NARROW"
                    elif raw_value >= 0.3:
                        q_type = "MEDIUM"
                    else:
                        q_type = "WIDE"
                        
                    self.log_message(f"Q TYPE: {q_type}")
            
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
            
            # Special handling for shape parameters to translate Pro-Q 3 values to Console1 values
            if "Shape" in param_name:
                # Get the current Pro-Q 3 raw value
                raw_value = param_value
                self.log_message(f"FEEDBACK REQUEST: Processing {param_name} with raw value {raw_value}")
                
                # Translate to MIDI value
                midi_value = self._translate_shape_to_midi(param_name, param_value)
            else:
                # Convert normal parameter value (0.0-1.0) to MIDI value (0-127)
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

    def _translate_shape_to_midi(self, param_name, param_value):
        """Translate Pro-Q 3 shape values to Console1 MIDI values"""
        # For Console1, we need to convert from Pro-Q 3 values to:
        # Shelf = 0, Bell = 63, Cut = 127
        
        # Bell = 0.0 (for both Band 2 and 5)
        # Low Shelf = 1.0 (for Band 2)
        # Low Cut = 2.0 (for Band 2)
        # High Shelf = 3.0 (for Band 5)
        # High Cut = 4.0 (for Band 5)
        
        # Debug the incoming value
        self.log_message(f"TRANSLATING: {param_name} with value {param_value} to MIDI")
        
        # Default to Bell (middle position)
        midi_value = SHAPE_BELL
        midi_label = "Bell"
        
        # Check which band we're dealing with
        if "Band 2" in param_name:
            # For Band 2
            if abs(param_value) < 0.1:  # Bell (0.0)
                midi_value = SHAPE_BELL  # 63
                midi_label = "Bell"
            elif abs(param_value - 1.0) < 0.1:  # Low Shelf (1.0)
                midi_value = SHAPE_SHELF  # 0
                midi_label = "Low Shelf"
            elif abs(param_value - 2.0) < 0.1:  # Low Cut (2.0)
                midi_value = SHAPE_CUT  # 127
                midi_label = "Low Cut"
        elif "Band 5" in param_name:
            # For Band 5
            if abs(param_value) < 0.1:  # Bell (0.0)
                midi_value = SHAPE_BELL  # 63
                midi_label = "Bell"
            elif abs(param_value - 3.0) < 0.1:  # High Shelf (3.0)
                midi_value = SHAPE_SHELF  # 0
                midi_label = "High Shelf"
            elif abs(param_value - 4.0) < 0.1:  # High Cut (4.0)
                midi_value = SHAPE_CUT  # 127
                midi_label = "High Cut"
        
        self.log_message(f"FEEDBACK: Translated {param_name} value {param_value} to MIDI {midi_value} ({midi_label})")
        return midi_value

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
        
        # Handle Q parameters (special buttons)
        if "Q" in param_name and param_name in self._param_refs:
            self._handle_q_parameter(param_name, value)
            return
        
        # Handle Device On parameter (Bypass button)
        if param_name == "Device On" and param_name in self._param_refs:
            self._handle_bypass_parameter(param_name, value)
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
        
        # Special handling for shape parameters (3-step toggle buttons)
        if "Shape" in param_name:
            self._handle_shape_parameter(param_name, value, param)
            return
        
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

    def _handle_shape_parameter(self, param_name, value, param):
        """Special handling for shape parameters (3-step toggle buttons)"""
        # Store the raw MIDI value
        self._last_midi_values[param_name] = value
        
        # Shape toggle buttons have 3 positions: Shelf (0), Bell (63), Cut (127)
        # Map from Console1 values to actual Pro-Q 3 parameter values
        
        # Pro-Q 3 actually uses different raw values for Band 2 and Band 5:
        # Bell = 0.0 (for both Band 2 and 5)
        # Low Shelf = 1.0 (for Band 2)
        # Low Cut = 2.0 (for Band 2)
        # High Shelf = 3.0 (for Band 5)
        # High Cut = 4.0 (for Band 5)
        
        # Bell is common for both bands
        PROQ3_BELL_VALUE = 0.0
        
        # Band 2 uses Low Shelf/Cut
        PROQ3_LOW_SHELF_VALUE = 1.0
        PROQ3_LOW_CUT_VALUE = 2.0
        
        # Band 5 uses High Shelf/Cut
        PROQ3_HIGH_SHELF_VALUE = 3.0
        PROQ3_HIGH_CUT_VALUE = 4.0
        
        shape_value = PROQ3_BELL_VALUE  # Default to Bell shape
        shape_name = "Bell"
        
        # Log the incoming MIDI value for debugging
        self.log_message(f"RECEIVED: {param_name} MIDI value {value}")
        
        # Different logic based on which band we're controlling
        if "Band 2" in param_name:
            # Band 2 uses Low Shelf/Cut
            if value == SHAPE_SHELF:  # Console1 value = 0
                shape_value = PROQ3_LOW_SHELF_VALUE
                shape_name = "Low Shelf"
            elif value == SHAPE_BELL:  # Console1 value = 63
                shape_value = PROQ3_BELL_VALUE
                shape_name = "Bell"
            elif value == SHAPE_CUT:  # Console1 value = 127
                shape_value = PROQ3_LOW_CUT_VALUE
                shape_name = "Low Cut"
            else:
                # For any intermediate values, map to the closest defined shape
                if value < SHAPE_BELL/2:
                    shape_value = PROQ3_LOW_SHELF_VALUE
                    shape_name = "Low Shelf"
                elif value < (SHAPE_BELL + SHAPE_CUT)/2:
                    shape_value = PROQ3_BELL_VALUE
                    shape_name = "Bell"
                else:
                    shape_value = PROQ3_LOW_CUT_VALUE
                    shape_name = "Low Cut"
        else:  # "Band 5" in param_name
            # Band 5 uses High Shelf/Cut
            if value == SHAPE_SHELF:  # Console1 value = 0
                shape_value = PROQ3_HIGH_SHELF_VALUE
                shape_name = "High Shelf"
            elif value == SHAPE_BELL:  # Console1 value = 63
                shape_value = PROQ3_BELL_VALUE
                shape_name = "Bell"
            elif value == SHAPE_CUT:  # Console1 value = 127
                shape_value = PROQ3_HIGH_CUT_VALUE
                shape_name = "High Cut"
            else:
                # For any intermediate values, map to the closest defined shape
                if value < SHAPE_BELL/2:
                    shape_value = PROQ3_HIGH_SHELF_VALUE
                    shape_name = "High Shelf"
                elif value < (SHAPE_BELL + SHAPE_CUT)/2:
                    shape_value = PROQ3_BELL_VALUE
                    shape_name = "Bell"
                else:
                    shape_value = PROQ3_HIGH_CUT_VALUE
                    shape_name = "High Cut"
        
        # Update our tracking value
        self._current_param_values[param_name] = shape_value
        
        # Log the shape change with raw value to help determine the actual Pro-Q 3 values
        self.log_message(f"SETTING {param_name} to {shape_name} (MIDI: {value}, Parameter: {shape_value})")
        
        # Update the parameter in Live
        param.value = shape_value
        
        # After setting value, directly read back the "actual" value that Live accepted
        actual_value = param.value
        if abs(actual_value - shape_value) > 0.01:
            self.log_message(f"NOTE: Pro-Q 3 adjusted value to {actual_value} (different from requested {shape_value})")

    def _handle_q_parameter(self, param_name, value):
        """Special handling for Q parameters from buttons"""
        # Store the raw MIDI value
        self._last_midi_values[param_name] = value
        
        # Log the incoming MIDI value
        self.log_message(f"RECEIVED: {param_name} MIDI value {value}")
        
        # Get the parameter
        param = self._param_refs[param_name]
        
        # Only respond to higher values to avoid multiple triggers when releasing the button
        if value < 64:  # Ignore button release (lower values)
            return
        
        # Get current Q value
        current_value = self._current_param_values[param_name]
        
        # Define Q presets (adjust these based on testing)
        # Q values typically range from narrow (high value) to wide (low value)
        Q_NARROW = 1.0   # Narrow Q
        Q_MEDIUM = 0.5   # Medium Q
        Q_WIDE = 0.1     # Wide Q
        
        # Cycle through Q presets each time the button is pressed
        if current_value >= 0.8:     # If current Q is narrow or close to it
            new_value = Q_MEDIUM     # Switch to medium
            q_label = "Medium"
        elif current_value >= 0.3:   # If current Q is medium or close to it
            new_value = Q_WIDE       # Switch to wide
            q_label = "Wide"
        else:                        # If current Q is wide or close to it
            new_value = Q_NARROW     # Switch to narrow
            q_label = "Narrow"
        
        # Update our tracking value
        self._current_param_values[param_name] = new_value
        
        # Log the Q change
        self.log_message(f"SETTING {param_name} to {q_label} (Value: {new_value})")
        
        # Update the parameter in Live
        self._parameter_value_changed_from_controller = True
        param.value = new_value

    def _handle_bypass_parameter(self, param_name, value):
        """Special handling for the Device On (bypass) parameter"""
        # Log the incoming MIDI value for debugging
        self.log_message(f"RECEIVED: {param_name} MIDI value {value}")
        
        # For this specific hardware, the button alternates between sending 127 and 0
        # But we want to toggle on every button press, regardless of the value
        
        # Store timestamp to prevent rapid repeated toggles (debouncing)
        # Use our own simple timestamp instead of Live.Base.Time
        current_time = time.time()
        last_time = getattr(self, '_last_bypass_time', 0)
        self._last_bypass_time = current_time
        
        # Implement debouncing - ignore events too close together (within 300ms)
        if current_time - last_time < 0.3:
            self.log_message(f"Ignoring bypass event - too soon after previous event")
            return
        
        # Since the hardware alternates between 127 and 0, we need to make sure
        # the incoming value is different from the last one to avoid double-triggers
        last_value = self._last_midi_values.get(param_name, -1)
        
        # Only process if the value is different from the last one we received
        if value == last_value:
            self.log_message(f"Ignoring duplicate bypass value {value}")
            return
        
        # Update the last value
        self._last_midi_values[param_name] = value
        
        # Get the parameter
        param = self._param_refs[param_name]
        
        # Get current state (1.0 = on, 0.0 = off/bypassed)
        current_value = self._current_param_values[param_name]
        
        # Toggle the bypass state
        new_value = 0.0 if current_value > 0.5 else 1.0
        
        # Update our tracking value
        self._current_param_values[param_name] = new_value
        
        # Log the state change
        state_label = "ON" if new_value > 0.5 else "BYPASSED"
        self.log_message(f"TOGGLING {param_name} to {state_label} (Value: {new_value})")
        
        # Update the parameter in Live
        self._parameter_value_changed_from_controller = True
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

    def _log_shape_mappings(self):
        """Log the shape and Q button mappings for debugging purposes"""
        # Import for local use to avoid circular imports
        from .Console1_Hardware import SHAPE_SHELF, SHAPE_BELL, SHAPE_CUT, BUTTON_EQ_BYPASS
        
        self.log_message("------ Console1 Control Mappings ------")
        self.log_message("MIDI-to-ProQ3 Shape Mappings:")
        self.log_message("Band 2:")
        self.log_message(f"- MIDI {SHAPE_SHELF} (Shelf) → ProQ3 1.0 (Low Shelf)")
        self.log_message(f"- MIDI {SHAPE_BELL} (Bell)  → ProQ3 0.0 (Bell)")
        self.log_message(f"- MIDI {SHAPE_CUT} (Cut)   → ProQ3 2.0 (Low Cut)")
        self.log_message("Band 5:")
        self.log_message(f"- MIDI {SHAPE_SHELF} (Shelf) → ProQ3 3.0 (High Shelf)")
        self.log_message(f"- MIDI {SHAPE_BELL} (Bell)  → ProQ3 0.0 (Bell)")
        self.log_message(f"- MIDI {SHAPE_CUT} (Cut)   → ProQ3 4.0 (High Cut)")
        
        # Q button mappings
        self.log_message("Q Button Mappings:")
        self.log_message("- CC 90 → Band 3 Q")
        self.log_message("- CC 87 → Band 4 Q")
        self.log_message("- Q Values: 0.1 (Wide), 0.5 (Medium), 1.0 (Narrow)")
        
        # Bypass button mapping
        self.log_message("Bypass Button Mapping:")
        self.log_message(f"- CC {BUTTON_EQ_BYPASS} → Device On/Bypass")
        self.log_message("-----------------------------------")