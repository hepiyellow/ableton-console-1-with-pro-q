from __future__ import with_statement

import Live
import time
from _Framework.ControlSurface import ControlSurface
from _Framework.InputControlElement import MIDI_CC_TYPE
from _Framework.SliderElement import SliderElement
from .ProQ3_MIDI_Map import PARAMETER_CC_MAP, MIDI_CHANNEL, ENABLE_DEBUG_LOGGING
from .Console1_Hardware import SHAPE_SHELF, SHAPE_BELL, SHAPE_CUT, BUTTON_EQ_BYPASS, CONTROL_NAMES
from .TrackControls_MIDI_Map import TRACK_CONTROL_MAP
from .APIVision_MIDI_Map import PARAMETER_CC_MAP as API_PARAMETER_CC_MAP
from .Neve1073_MIDI_Map import PARAMETER_CC_MAP as NEVE_PARAMETER_CC_MAP

# Device type constants
DEVICE_PRO_Q3 = "Pro-Q 3"
DEVICE_API_VISION = "UADx API Vision Channel Strip"
DEVICE_NEVE_1073 = "UADx Neve 1073 Preamp and EQ"

class Console1DeviceControl(ControlSurface):
    __doc__ = " Console1DeviceControl script that controls Pro-Q 3 and other device parameters with encoders "

    _active_instances = []
    
    # Supported devices in order of priority
    DEVICE_ORDER = [DEVICE_PRO_Q3, DEVICE_API_VISION, DEVICE_NEVE_1073]
    
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
        self.log_message("Console1DeviceControl: Loaded successfully!")
        
        # Store device references
        self._resolved_device = None
        self._resolved_device_type = None
        self._has_track_listener = False
        self._has_device_listeners = False  # Track if device listeners are connected
        self._sending_feedback = False  # Flag to prevent feedback loops
        self._has_param_listener = False  # Track if parameter listener is connected
        self._parameter_value_changed_from_controller = False  # Flag to track source of value changes
        self._debug_logging = True  # ALWAYS enable debug logging to troubleshoot Q issue
        
        # Get parameter CC maps from the imported mapping files
        self._proq3_cc_map = PARAMETER_CC_MAP
        self._api_cc_map = API_PARAMETER_CC_MAP
        self._neve_cc_map = NEVE_PARAMETER_CC_MAP
        self._track_control_map = TRACK_CONTROL_MAP
        
        # Create mapping of device types to parameter maps
        self._device_param_maps = {
            DEVICE_PRO_Q3: self._proq3_cc_map,
            DEVICE_API_VISION: self._api_cc_map,
            DEVICE_NEVE_1073: self._neve_cc_map
        }
        
        # Create reverse mappings for CC to parameter name lookup for each device
        cc_to_proq3_param = {config['cc']: param for param, config in self._proq3_cc_map.items()}
        cc_to_api_param = {config['cc']: param for param, config in self._api_cc_map.items()}
        cc_to_neve_param = {config['cc']: param for param, config in self._neve_cc_map.items()}
        cc_to_track_param = {cc: param for param, cc in self._track_control_map.items()}
        
        # Store the reverse mappings for later use
        self._cc_to_proq3_param = cc_to_proq3_param
        self._cc_to_api_param = cc_to_api_param
        self._cc_to_neve_param = cc_to_neve_param
        self._cc_to_track_param = cc_to_track_param
        
        # Create mapping of device types to CC-to-parameter maps
        self._device_cc_to_param_maps = {
            DEVICE_PRO_Q3: self._cc_to_proq3_param,
            DEVICE_API_VISION: self._cc_to_api_param,
            DEVICE_NEVE_1073: self._cc_to_neve_param
        }
        
        # Initially use Pro-Q 3 mapping as default
        self._param_cc_map = self._proq3_cc_map
        
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
            
            # Create encoders and set up listeners for all possible mappings
            self._setup_encoders()
            
            # Safely add track change listener
            self._setup_track_listener()
            
            # Schedule the initial device setup to run after Live has fully loaded
            self.schedule_message(1, self._initial_device_setup)
            
            # Log shape mapping for debugging
            self.schedule_message(2, self._log_shape_mappings)
            
            # Log the mode we're in
            mode_str = "relative (stepped)" if self.EMULATE_RELATIVE_MODE else "absolute (0-127)"
            self.log_message(f"Console1DeviceControl: Encoder mode set to {mode_str}")
            self.log_message("Console1DeviceControl: Setup complete, listening for encoder messages")
    
    def debug_log(self, *message):
        """Log message only if debug logging is enabled"""
        if self._debug_logging:
            self.log_message(*message)
    
    def _setup_encoders(self):
        """Create encoder elements and set up listeners based on hardware controls"""
        # Import hardware definitions
        from .Console1_Hardware import CONTROL_NAMES
        
        self.log_message("Setting up hardware CC-based encoders")
        
        # Log mappings for debugging - can be removed in production
        for cc, param in self._cc_to_proq3_param.items():
            control_name = CONTROL_NAMES.get(cc, f"CC {cc}")
            self.debug_log(f"Pro-Q 3: {control_name} (CC {cc}) -> {param}")
        
        # Set up encoders for all hardware controls based on CC numbers from CONTROL_NAMES
        # This makes our system CC-based rather than parameter-name based
        self._cc_encoders = {}  # Store encoders by CC number
        
        for cc_number, control_name in CONTROL_NAMES.items():
            self.log_message(f"Setting up encoder for {control_name} (CC {cc_number})")
            
            # Create a slider element for this CC number
            encoder = SliderElement(MIDI_CC_TYPE, self._midi_channel, cc_number)
            
            # Store the encoder in our CC dictionary
            self._cc_encoders[cc_number] = encoder
            
            # Add value listener with a closure to capture just the CC number
            def create_cc_listener(cc=cc_number):
                def listener(value):
                    self._on_cc_value(cc, value)
                return listener
            
            # Add the value listener
            encoder.add_value_listener(create_cc_listener())
            
            self.debug_log(f"Set up encoder for CC {cc_number} ({control_name})")
        
        # Initialize tracking values
        self._last_cc_values = {}  # Last CC values by CC number
        self._current_param_values = {}  # Current parameter values by param name
        
    def _on_cc_value(self, cc_number, value):
        """Called when a CC value is received from the hardware"""
        # Skip if we're in the middle of sending feedback to avoid loops
        if self._sending_feedback:
            return
            
        # Log the current resolved device and CC received
        from .Console1_Hardware import CONTROL_NAMES, KNOB_VOLUME, BUTTON_TRACK_SOLO, BUTTON_TRACK_MUTE
        control_name = CONTROL_NAMES.get(cc_number, f"CC {cc_number}")
        device_info = f"Current device: {self._resolved_device_type}" if self._resolved_device_type else "No device resolved"
        self.log_message(f"MIDI received - {device_info} - CC {cc_number} ({control_name}) Value {value}")
        
        # Determine which parameter this CC controls in the current device
        param_name = None
        
        # First check track controls
        if cc_number in self._cc_to_track_param:
            param_name = self._cc_to_track_param[cc_number]
            self.debug_log(f"CC {cc_number} maps to track control: {param_name}")
            
            # Handle track controls
            if param_name == "Volume":
                self._handle_track_volume(value)
                return
            elif param_name == "Track Solo":
                self._handle_track_solo(value)
                return
            elif param_name == "Track Mute":
                self._handle_track_mute(value)
                return
        
        # If no resolved device, we can't control device parameters
        if not self._resolved_device:
            self.debug_log(f"No device resolved, ignoring CC {cc_number}")
            return
            
        # Check the resolved device's mapping using the dictionary
        if self._resolved_device_type in self._device_cc_to_param_maps:
            cc_to_param_map = self._device_cc_to_param_maps[self._resolved_device_type]
            if cc_number in cc_to_param_map:
                param_name = cc_to_param_map[cc_number]
            else:
                param_name = None
        else:
            param_name = None
        
        # If we found a parameter, handle it
        if param_name:
            self.debug_log(f"CC {cc_number} maps to {self._resolved_device_type} parameter: {param_name}")
            
            # Handle Device On parameter (Bypass button)
            if param_name == "Device On" and param_name in self._param_refs:
                self._handle_bypass_parameter(param_name, value)
                return
                
            # Handle device parameters only if they exist in the device
            if param_name in self._param_refs:
                # Extra debug for Q parameters in Pro-Q 3
                if "Q" in param_name and self._resolved_device_type == "Pro-Q 3":
                    self.log_message(f"CALLING _handle_parameter_change for {param_name}")
                self._handle_parameter_change(param_name, value)
            else:
                self.debug_log(f"Parameter {param_name} not found in current device")
        else:
            # This CC doesn't map to any parameter in the current device
            self.debug_log(f"CC {cc_number} not mapped to any parameter in {self._resolved_device_type}")
                
        # Store the last received value for this CC
        self._last_cc_values[cc_number] = value
        
    def _determine_relative_change(self, cc_number, new_value):
        """Determine the relative change direction based on current and new MIDI values"""
        last_value = self._last_cc_values.get(cc_number, -1)
        
        # If we don't have a previous value, just store this one and return no change
        if last_value == -1:
            self._last_cc_values[cc_number] = new_value
            return 0
        
        # Store the new value
        self._last_cc_values[cc_number] = new_value
        
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
        
    def _handle_track_volume(self, value):
        """Handle track volume encoder events"""
        # Only respond if we have a current track
        if not self._current_track:
            self.debug_log("No current track selected")
            return
        
        try:
            # Get the volume parameter from the track
            volume_param = self._current_track.mixer_device.volume
            
            # For volume, we want to use absolute or relative mode based on the global setting
            if self.EMULATE_RELATIVE_MODE:
                # Relative mode (stepped)
                from .Console1_Hardware import KNOB_VOLUME
                change_direction = self._determine_relative_change(KNOB_VOLUME, value)
                if change_direction == 0:
                    return
                
                # Get current volume
                current_value = volume_param.value
                
                # Calculate new value
                new_value = current_value + (change_direction * self.PARAMETER_STEP_SIZE)
                new_value = max(0.0, min(1.0, new_value))
                
                self.debug_log(f"Track Volume - Direction: {change_direction}, " + 
                               f"Old: {current_value:.3f}, New: {new_value:.3f}")
            else:
                # Absolute mode (0-127)
                from .Console1_Hardware import KNOB_VOLUME
                self._last_cc_values[KNOB_VOLUME] = value
                new_value = value / 127.0
                self.debug_log(f"Track Volume - Absolute: {value}, Value: {new_value:.3f}")
            
            # Update the parameter in Live
            self._parameter_value_changed_from_controller = True
            volume_param.value = new_value
        except Exception as e:
            self.log_message(f"Error adjusting track volume: {str(e)}")
            
    def _send_simple_feedback(self, cc_number, value, silent=False):
        """Send a simple MIDI value as feedback to the controller"""
        if cc_number not in self._cc_encoders:
            return
        
        try:
            # Prevent feedback loops
            if self._sending_feedback:
                return
            
            self._sending_feedback = True
            
            # Send the value to the controller
            self._cc_encoders[cc_number].send_value(value)
            
            # Update last value to avoid ping-pong
            self._last_cc_values[cc_number] = value
            
            # Log only if not silent and debugging is enabled
            if not silent and self._debug_logging:
                from .Console1_Hardware import CONTROL_NAMES
                control_name = CONTROL_NAMES.get(cc_number, f"CC {cc_number}")
                self.debug_log(f"Sending feedback for {control_name} (CC {cc_number}), MIDI value: {value}")
            
            self._sending_feedback = False
        except Exception as e:
            self._sending_feedback = False
            self.log_message(f"Error sending feedback for CC {cc_number}:", str(e))
            
    def _handle_track_solo(self, value):
        """Handle track solo button events"""
        # Log the incoming MIDI value for debugging
        self.log_message(f"RECEIVED: Track Solo value {value}")
        
        # Only respond if we have a current track
        if not self._current_track:
            self.log_message("No current track selected")
            return
        
        # Since the hardware alternates values like the bypass button,
        # we'll only toggle on a value change, not on specific values
        from .Console1_Hardware import BUTTON_TRACK_SOLO
        last_value = self._last_cc_values.get(BUTTON_TRACK_SOLO, -1)
        
        # Store the current value
        self._last_cc_values[BUTTON_TRACK_SOLO] = value
        
        # Debounce to prevent multiple toggles
        current_time = time.time()
        last_time = getattr(self, '_last_solo_time', 0)
        self._last_solo_time = current_time
        
        # Ignore events too close together (within 300ms)
        if current_time - last_time < 0.3:
            self.log_message(f"Ignoring solo event - too soon after previous event")
            return
        
        # Only process if the value is different from the last one
        if value == last_value:
            self.log_message(f"Ignoring duplicate solo value {value}")
            return
        
        # Toggle the track's solo state
        try:
            current_state = self._current_track.solo
            new_state = not current_state
            self._current_track.solo = new_state
            
            # Log the state change
            state_str = "ON" if new_state else "OFF"
            self.log_message(f"TOGGLING Track Solo to {state_str} for track: {self._current_track.name}")
            
            # Send feedback to the controller
            feedback_value = 127 if new_state else 0
            self._send_simple_feedback(BUTTON_TRACK_SOLO, feedback_value)
        except Exception as e:
            self.log_message(f"Error toggling track solo: {str(e)}")
            
    def _handle_track_mute(self, value):
        """Handle track mute button events"""
        # Log the incoming MIDI value for debugging
        self.log_message(f"RECEIVED: Track Mute value {value}")
        
        # Only respond if we have a current track
        if not self._current_track:
            self.log_message("No current track selected")
            return
        
        # Since the hardware alternates values like the bypass button,
        # we'll only toggle on a value change, not on specific values
        from .Console1_Hardware import BUTTON_TRACK_MUTE
        last_value = self._last_cc_values.get(BUTTON_TRACK_MUTE, -1)
        
        # Store the current value
        self._last_cc_values[BUTTON_TRACK_MUTE] = value
        
        # Debounce to prevent multiple toggles
        current_time = time.time()
        last_time = getattr(self, '_last_mute_time', 0)
        self._last_mute_time = current_time
        
        # Ignore events too close together (within 300ms)
        if current_time - last_time < 0.3:
            self.log_message(f"Ignoring mute event - too soon after previous event")
            return
        
        # Only process if the value is different from the last one
        if value == last_value:
            self.log_message(f"Ignoring duplicate mute value {value}")
            return
        
        # Toggle the track's mute state
        try:
            current_state = self._current_track.mute
            new_state = not current_state
            self._current_track.mute = new_state
            
            # Log the state change
            state_str = "ON" if new_state else "OFF"
            self.log_message(f"TOGGLING Track Mute to {state_str} for track: {self._current_track.name}")
            
            # Send feedback to the controller
            feedback_value = 127 if new_state else 0
            self._send_simple_feedback(BUTTON_TRACK_MUTE, feedback_value)
        except Exception as e:
            self.log_message(f"Error toggling track mute: {str(e)}")
            
    def _send_track_state_feedback(self):
        """Send feedback to the controller for track state (solo/mute)"""
        if not self._current_track:
            return
        
        try:
            from .Console1_Hardware import KNOB_VOLUME, BUTTON_TRACK_SOLO, BUTTON_TRACK_MUTE
            
            # Send Volume feedback
            if KNOB_VOLUME in self._cc_encoders and hasattr(self._current_track.mixer_device, 'volume'):
                volume_value = self._current_track.mixer_device.volume.value
                midi_value = int(volume_value * 127)
                self._send_simple_feedback(KNOB_VOLUME, midi_value)
                self.debug_log(f"Sent Volume feedback: {midi_value} for track: {self._current_track.name}")
                
            # Send Solo state feedback
            if BUTTON_TRACK_SOLO in self._cc_encoders:
                # Solo is on = 127, off = 0
                solo_value = 127 if self._current_track.solo else 0
                self._send_simple_feedback(BUTTON_TRACK_SOLO, solo_value)
                self.debug_log(f"Sent Solo feedback: {solo_value} for track: {self._current_track.name}")
                
            # Send Mute state feedback
            if BUTTON_TRACK_MUTE in self._cc_encoders:
                # Mute is on = 127, off = 0
                mute_value = 127 if self._current_track.mute else 0
                self._send_simple_feedback(BUTTON_TRACK_MUTE, mute_value)
                self.debug_log(f"Sent Mute feedback: {mute_value} for track: {self._current_track.name}")
        except Exception as e:
            self.log_message(f"Error sending track state feedback: {str(e)}")
            
    def _send_parameter_feedback(self, param_name, param_value, silent=False):
        """Send feedback to the controller with the current parameter value"""
        # Find which CC number controls this parameter in the current device
        cc_config = None
        
        # Check in the appropriate mapping based on the current device
        if self._resolved_device_type in self._device_param_maps:
            cc_config = self._device_param_maps[self._resolved_device_type].get(param_name)
        
        if cc_config is None:
            return
        
        cc_number = cc_config['cc']
        invert = cc_config.get('invert', False)
        
        # Log inversion status for debugging
        if "Freq" in param_name and self._resolved_device_type == DEVICE_API_VISION:
            self.log_message(f"*** FEEDBACK INVERT: {param_name} has invert={invert}, config={cc_config}")
        
        if cc_number not in self._cc_encoders:
            return
        
        try:
            # Prevent feedback loops
            if self._sending_feedback:
                return
                
            self._sending_feedback = True
            
            # Get the parameter to check if it's discrete
            param = self._param_refs.get(param_name)
            
            # Safely check if parameter is discrete (quantized with value_items)
            is_discrete = False
            try:
                is_discrete = param and hasattr(param, 'is_quantized') and param.is_quantized and hasattr(param, 'value_items')
            except Exception as e:
                self.log_message(f"Error checking if {param_name} is discrete for feedback: {str(e)}")
            
            # Special handling for shape parameters to translate Pro-Q 3 values to Console1 values
            if "Shape" in param_name and self._resolved_device_type == "Pro-Q 3":
                # Get the current Pro-Q 3 raw value
                raw_value = param_value
                self.log_message(f"FEEDBACK REQUEST: Processing {param_name} with raw value {raw_value}")
                
                # Translate to MIDI value
                midi_value = self._translate_shape_to_midi(param_name, param_value)
            elif is_discrete:
                # Handle discrete parameter feedback
                # Get the total number of possible values
                num_values = len(param.value_items)
                
                # Get the current index (make sure it's an integer)
                current_index = int(param_value)
                
                # Map the index to a MIDI value (0-127)
                # This distributes the indices evenly across the MIDI range
                if num_values > 1:
                    # Calculate normalized index position (0-1 range)
                    normalized_index = current_index / float(num_values - 1)
                    
                    # Apply inversion if needed
                    if invert:
                        normalized_index = 1.0 - normalized_index
                        self.log_message(f"*** DISCRETE FEEDBACK INVERT: {param_name}, Original idx: {current_index}, Normalized: {normalized_index:.3f}")
                        
                    # Convert to MIDI value
                    midi_value = int(normalized_index * 127.0)
                else:
                    midi_value = 0
                
                invert_str = " (inverted)" if invert else ""
                self.log_message(f"DISCRETE FEEDBACK{invert_str}: {param_name}, Index: {current_index}, Items: {num_values}, MIDI: {midi_value}")
            else:
                # Convert normal parameter value (0.0-1.0) to MIDI value (0-127)
                # Invert the value if needed
                feedback_value = 1.0 - param_value if invert else param_value
                midi_value = int(feedback_value * 127)
                
                # For all frequency parameters, log feedback values
                if "Freq" in param_name and self._resolved_device_type == "UADx API Vision Channel Strip":
                    if invert:
                        self.log_message(f"*** FEEDBACK INVERSION APPLIED: {param_name}, Original: {param_value:.3f}, Inverted: {feedback_value:.3f}, MIDI: {midi_value}")
                    else:
                        self.log_message(f"*** NO FEEDBACK INVERSION: {param_name}, Value: {param_value:.3f}, MIDI: {midi_value}")
                # For other inverted parameters, add standard logging
                elif invert:
                    self.log_message(f"INVERTED FEEDBACK: {param_name}, Original: {param_value:.3f}, Inverted: {feedback_value:.3f}, MIDI: {midi_value}")
            
            # Log message only if not silent and debug logging is enabled
            if not silent and self._debug_logging:
                from .Console1_Hardware import CONTROL_NAMES
                control_name = CONTROL_NAMES.get(cc_number, f"CC {cc_number}")
                invert_str = " (inverted)" if invert else ""
                self.debug_log(f"Sending feedback for {param_name}{invert_str} via {control_name} (CC {cc_number}), MIDI value: {midi_value}")
            
            # Send the value back to the controller
            self._cc_encoders[cc_number].send_value(midi_value)
            
            # Update last value to avoid ping-pong
            self._last_cc_values[cc_number] = midi_value
            
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

    def _initial_device_setup(self):
        """Initialize device and parameter setup on script load"""
        self.debug_log("Running initial device setup")
        
        # First check the currently selected track
        self._on_selected_track_changed()
        
        # If we didn't find a supported device on the selected track, search all tracks
        if not self._resolved_device:
            self.debug_log("No supported device found on selected track, searching all tracks")
            self._find_device_on_any_track()
        
        # Set up device listeners to detect when supported devices are added later
        self._setup_device_listeners()

    def _find_device_in_rack(self, device, track):
        """Recursively search for supported devices within a rack based on priority order"""
        # Check if this device is in our supported list
        if device.name in self.DEVICE_ORDER:
            device_type = device.name
            device_priority = self.DEVICE_ORDER.index(device_type)
            
            # Safely get current priority (handling None case)
            if self._resolved_device is None or self._resolved_device_type is None:
                current_priority = float('inf')
            else:
                current_priority = self.DEVICE_ORDER.index(self._resolved_device_type)
            
            # If we haven't found a device yet or this one has higher priority
            if self._resolved_device is None or device_priority < current_priority:
                self._resolved_device = device
                self._resolved_device_type = device_type
                self._current_track = track
                self.log_message(f"Found {device_type} in rack on track: {track.name}")
                return True
        
        # Check if this device is a rack with chains
        if hasattr(device, 'chains') and len(device.chains) > 0:
            # Look through all chains in the rack
            for chain in device.chains:
                # Look through all devices in the chain
                for chain_device in chain.devices:
                    # Recursive search in each device
                    if self._find_device_in_rack(chain_device, track):
                        return True
        return False

    def _find_device_on_any_track(self):
        """Search all tracks for supported devices in priority order"""
        try:
            # Reset device resolution
            self._resolved_device = None
            self._resolved_device_type = None
            
            # Look through all tracks in the session
            for track_index, track in enumerate(self.song().tracks):
                self.debug_log("Checking track:", track.name)
                
                # Find supported devices in track's devices (direct or in racks)
                for device in track.devices:
                    if device.name in self.DEVICE_ORDER:
                        device_type = device.name
                        device_priority = self.DEVICE_ORDER.index(device_type)
                        
                        # Safely get current priority (handling None case)
                        if self._resolved_device is None or self._resolved_device_type is None:
                            current_priority = float('inf')
                        else:
                            current_priority = self.DEVICE_ORDER.index(self._resolved_device_type)
                        
                        # If we haven't found a device yet or this one has higher priority
                        if self._resolved_device is None or device_priority < current_priority:
                            self._resolved_device = device
                            self._resolved_device_type = device_type
                            self._current_track = track
                            self.log_message(f"Found {device_type} on track: {track.name}")
                    
                    # Also check inside racks
                    elif hasattr(device, 'chains'):
                        self._find_device_in_rack(device, track)
                
                # If we found a highest priority device, select its track
                if self._resolved_device and self._resolved_device_type == self.DEVICE_ORDER[0]:
                    self.song().view.selected_track = track
                    self._setup_device_parameters(self._resolved_device)
                    return True
                
            # If we didn't find the highest priority device but found something else,
            # use what we found
            if self._resolved_device:
                self.song().view.selected_track = self._current_track
                self._setup_device_parameters(self._resolved_device)
                return True
                
            # Also search return tracks
            for track in self.song().return_tracks:
                self.debug_log("Checking return track:", track.name)
                
                # Find supported devices in track's devices (direct or in racks)
                for device in track.devices:
                    if device.name in self.DEVICE_ORDER:
                        device_type = device.name
                        device_priority = self.DEVICE_ORDER.index(device_type)
                        
                        # Safely get current priority (handling None case)
                        if self._resolved_device is None or self._resolved_device_type is None:
                            current_priority = float('inf')
                        else:
                            current_priority = self.DEVICE_ORDER.index(self._resolved_device_type)
                        
                        # If we haven't found a device yet or this one has higher priority
                        if self._resolved_device is None or device_priority < current_priority:
                            self._resolved_device = device
                            self._resolved_device_type = device_type
                            self._current_track = track
                            self.log_message(f"Found {device_type} on return track: {track.name}")
                    
                    # Also check inside racks
                    elif hasattr(device, 'chains'):
                        self._find_device_in_rack(device, track)
            
            # Check master track
            master_track = self.song().master_track
            self.debug_log("Checking master track")
            
            # Find supported devices in master track's devices (direct or in racks)
            for device in master_track.devices:
                if device.name in self.DEVICE_ORDER:
                    device_type = device.name
                    device_priority = self.DEVICE_ORDER.index(device_type)
                    
                    # Safely get current priority (handling None case)
                    if self._resolved_device is None or self._resolved_device_type is None:
                        current_priority = float('inf')
                    else:
                        current_priority = self.DEVICE_ORDER.index(self._resolved_device_type)
                    
                    # If we haven't found a device yet or this one has higher priority
                    if self._resolved_device is None or device_priority < current_priority:
                        self._resolved_device = device
                        self._resolved_device_type = device_type
                        self._current_track = master_track
                        self.log_message(f"Found {device_type} on master track")
                
                # Also check inside racks
                elif hasattr(device, 'chains'):
                    self._find_device_in_rack(device, master_track)
            
            # If we found any supported device, select its track and set up parameters
            if self._resolved_device:
                self.song().view.selected_track = self._current_track
                self._setup_device_parameters(self._resolved_device)
                return True
            
            self.log_message("Could not find any supported device on any track")
            return False
            
        except Exception as e:
            self.log_message("Error in global device search:", str(e))
            return False

    def _setup_track_volume(self, track):
        """Set up volume parameter for the specified track"""
        try:
            if track and track.mixer_device and hasattr(track.mixer_device, 'volume'):
                from .Console1_Hardware import KNOB_VOLUME
                volume_param = track.mixer_device.volume
                current_value = volume_param.value
                self.debug_log(f"Found Volume parameter for track: {track.name}, current value: {current_value}")
                
                # Send feedback to controller with current parameter value (silent)
                self._send_simple_feedback(KNOB_VOLUME, int(current_value * 127), silent=True)
                
                # Setup track state listeners for solo/mute
                self._setup_track_state_listeners(track)
                
                return True
            return False
        except Exception as e:
            self.log_message("Error setting up track volume:", str(e))
            return False

    def _setup_track_state_listeners(self, track):
        """Set up listeners for track state changes (solo/mute)"""
        try:
            # Add solo listener
            if hasattr(track, 'add_solo_listener'):
                track.add_solo_listener(self._on_track_solo_changed)
                self.debug_log(f"Added solo listener to track: {track.name}")
                
            # Add mute listener
            if hasattr(track, 'add_mute_listener'):
                track.add_mute_listener(self._on_track_mute_changed)
                self.debug_log(f"Added mute listener to track: {track.name}")
                
            # Store reference to know which track has listeners
            self._track_with_listeners = track
                
        except Exception as e:
            self.log_message(f"Error setting up track state listeners: {str(e)}")

    def _remove_track_state_listeners(self):
        """Remove track state listeners from previous track"""
        if hasattr(self, '_track_with_listeners') and self._track_with_listeners:
            try:
                track = self._track_with_listeners
                
                # Remove solo listener
                if hasattr(track, 'remove_solo_listener'):
                    try:
                        track.remove_solo_listener(self._on_track_solo_changed)
                        self.debug_log(f"Removed solo listener from track: {track.name}")
                    except:
                        pass
                    
                # Remove mute listener
                if hasattr(track, 'remove_mute_listener'):
                    try:
                        track.remove_mute_listener(self._on_track_mute_changed)
                        self.debug_log(f"Removed mute listener from track: {track.name}")
                    except:
                        pass
                    
                self._track_with_listeners = None
                
            except Exception as e:
                self.log_message(f"Error removing track state listeners: {str(e)}")

    def _on_track_solo_changed(self):
        """Called when the solo state of the current track changes in Live"""
        if not self._current_track:
            return
        
        # Send feedback for the new solo state
        try:
            from .Console1_Hardware import BUTTON_TRACK_SOLO
            solo_state = self._current_track.solo
            self.debug_log(f"Track solo changed to: {solo_state} for track: {self._current_track.name}")
            
            # Send feedback to the controller
            feedback_value = 127 if solo_state else 0
            self._send_simple_feedback(BUTTON_TRACK_SOLO, feedback_value)
        except Exception as e:
            self.log_message(f"Error handling solo change: {str(e)}")

    def _on_track_mute_changed(self):
        """Called when the mute state of the current track changes in Live"""
        if not self._current_track:
            return
        
        # Send feedback for the new mute state
        try:
            from .Console1_Hardware import BUTTON_TRACK_MUTE
            mute_state = self._current_track.mute
            self.debug_log(f"Track mute changed to: {mute_state} for track: {self._current_track.name}")
            
            # Send feedback to the controller
            feedback_value = 127 if mute_state else 0
            self._send_simple_feedback(BUTTON_TRACK_MUTE, feedback_value)
        except Exception as e:
            self.log_message(f"Error handling mute change: {str(e)}")

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

    def _on_param_value_changed(self, param_name):
        """Called when a parameter value changes in Live (not from controller)"""
        try:
            # Skip processing if the change was initiated by our controller
            if self._parameter_value_changed_from_controller:
                self._parameter_value_changed_from_controller = False
                return
                
            # Get the parameter
            if param_name not in self._param_refs:
                self.debug_log(f"Parameter {param_name} not found in references")
                return
                
            param = self._param_refs[param_name]
            current_value = param.value
            
            # Update our tracking value
            self._current_param_values[param_name] = current_value
            
            # Log the change
            self.debug_log(f"Parameter {param_name} changed in Live to {current_value:.3f}")
            
            # Send feedback to the controller to update its display/LEDs
            self._send_parameter_feedback(param_name, current_value)
            
        except Exception as e:
            self.log_message(f"Error in parameter value change handler: {str(e)}")

    def _log_devices_in_rack(self, rack_device, indent=0):
        """Log the devices nested inside a rack with proper indentation"""
        indent_str = "  " * indent  # Two spaces per level
        
        for chain_index, chain in enumerate(rack_device.chains):
            self.log_message(f"{indent_str}Chain {chain_index+1}:")
            
            for device_index, device in enumerate(chain.devices):
                self.log_message(f"{indent_str}  Device {device_index+1}: {device.name}")
                
                # Recursive logging for nested racks
                if hasattr(device, 'chains') and len(device.chains) > 0:
                    self._log_devices_in_rack(device, indent=indent+2)
    
    def _on_selected_track_changed(self):
        """Called when the selected track changes in Live"""
        self.log_message("Track selection changed")
        
        # Clean up existing parameter listeners
        self._remove_parameter_listeners()
        
        # Remove track state listeners from previous track
        self._remove_track_state_listeners()
        
        # Reset device reference but keep Volume parameter separate
        self._resolved_device = None
        self._resolved_device_type = None
        self._param_refs = {}
        
        try:
            track = self.song().view.selected_track
            self._current_track = track
            self.log_message(f"Selected track: {track.name}")
            
            # Log all devices on the track
            self.log_message("=== DEVICES ON TRACK ===")
            if hasattr(track, 'devices') and len(track.devices) > 0:
                for i, device in enumerate(track.devices):
                    self.log_message(f"Device {i+1}: {device.name}")
                    
                    # Also log devices in racks
                    if hasattr(device, 'chains') and len(device.chains) > 0:
                        self._log_devices_in_rack(device, indent=1)
            else:
                self.log_message("No devices on this track")
            self.log_message("==========================")
            
            # Set up volume parameter for the new track
            self._setup_track_volume(track)
            
            # Explicitly send feedback for track state (solo/mute)
            # This ensures the controller LEDs update when changing tracks
            self._send_track_state_feedback()
            
            # Find supported devices in priority order
            device_found = False
            
            # First search for devices in priority order
            for device_type in self.DEVICE_ORDER:
                # Check direct devices first
                for device in track.devices:
                    if device.name == device_type:
                        self._resolved_device = device
                        self._resolved_device_type = device_type
                        self.log_message(f"Found {device_type} on track: {track.name}")
                        
                        # Find parameters and set up listeners
                        self._setup_device_parameters(device)
                        device_found = True
                        break
                
                # If highest priority device found, stop looking
                if device_found:
                    break
            
            # If not found directly, check for devices in racks
            if not device_found:
                for device in track.devices:
                    if hasattr(device, 'chains') and len(device.chains) > 0:
                        # This is a rack, search inside it
                        if self._find_device_in_rack(device, track):
                            device_found = True
                            self._setup_device_parameters(self._resolved_device)
                            break
                            
            # Log the resolved device after track change
            if device_found:
                self.log_message(f"Track changed - Now controlling: {self._resolved_device_type}")
            else:
                self.log_message("Track changed - No supported devices found, only track controls available")
                self.debug_log(f"No supported devices found on track: {track.name}")
                # Even with no device, we still have the Volume parameter set up above
                self.log_message(f"Track volume control active for: {track.name}")
        except Exception as e:
            self.log_message("Error in track change handler:", str(e))

    def _setup_device_parameters(self, device):
        """Find all device parameters needed and set up listeners"""
        try:
            device_type = device.name
            self.debug_log(f"Setting up parameters for {device_type}")
            
            # Use the appropriate parameter map based on device type
            if device_type in self._device_param_maps:
                self._param_cc_map = self._device_param_maps[device_type]
                self.log_message(f"Using {device_type} MIDI mapping")
            else:
                # Default to Pro-Q 3 if device type is not recognized
                self._param_cc_map = self._proq3_cc_map
                self.log_message(f"Device {device_type} not recognized, using {DEVICE_PRO_Q3} MIDI mapping as default")
            
            # Find all device parameters we need
            for param_name in self._param_cc_map.keys():
                # Skip Volume parameter as it's handled separately in _setup_track_volume
                if param_name == "Volume":
                    continue
                    
                found_param = False
                for param in device.parameters:
                    if param.name == param_name:
                        found_param = True
                        self._param_refs[param_name] = param
                        current_value = param.value
                        self._current_param_values[param_name] = current_value
                        
                        # Special logging for Q parameters when using Pro-Q 3
                        if "Q" in param_name and device_type == "Pro-Q 3":
                            self.log_message(f"FOUND Q PARAMETER: {param_name}, value: {current_value}")
                        else:
                            self.debug_log(f"Found {param_name} parameter, value: {current_value}")
                        
                        # Send feedback to controller with current parameter value (silent)
                        # Send feedback for all parameters - we use param_cc_map to find CC
                        self._send_parameter_feedback(param_name, current_value, silent=True)
                        
                        # Add value listener to the parameter to update when Live changes the value
                        self._setup_parameter_listener(param_name, param)
                        
                        break
                
                # Check if we found the parameter
                if not found_param and param_name != "Volume":
                    # Extra logging for Q parameters with Pro-Q 3
                    if "Q" in param_name and device_type == "Pro-Q 3":
                        self.log_message(f"WARNING: Could not find Q parameter: {param_name}")
                        # List all available parameters
                        self.log_message("AVAILABLE PARAMETERS:")
                        for idx, p in enumerate(device.parameters):
                            self.log_message(f"{idx}: {p.name}")
                    else:
                        self.debug_log(f"Could not find {param_name} parameter")
            
            # Log summary of found parameters
            found_params = sum(1 for name in self._param_refs if name != "Volume")
            total_params = len(self._param_cc_map) - (1 if "Volume" in self._param_cc_map else 0)
            self.log_message(f"Found {found_params} of {total_params} parameters for {device_type}")
            
            # Explicitly send feedback for all parameters to update controller
            self.log_message("Sending initial feedback for all parameters")
            for param_name, param in self._param_refs.items():
                if param_name != "Volume":  # Skip Volume as it's handled separately
                    try:
                        current_value = param.value
                        self._send_parameter_feedback(param_name, current_value, silent=False)
                    except Exception as e:
                        self.log_message(f"Error sending initial feedback for {param_name}: {str(e)}")
            
            # List which Q parameters were found (Pro-Q 3 specific)
            if device_type == "Pro-Q 3":
                q_params_found = [name for name in self._param_refs if "Q" in name]
                self.log_message(f"Q parameters found: {q_params_found}")
                
        except Exception as e:
            self.log_message(f"Error setting up {device_type} parameters:", str(e))
            
    def _handle_parameter_change(self, param_name, value):
        """Handle parameter value changes from encoder movement"""
        # Log all parameter changes for debugging
        self.log_message(f"Parameter change: {param_name}, MIDI value: {value}")
        
        # Extra specific logging for Q parameters to ensure continuous control
        if "Q" in param_name and self._resolved_device_type == "Pro-Q 3":
            # Log raw values for debugging
            self.log_message(f"Q PARAMETER CHANGE: {param_name}, MIDI value: {value}, raw")
            
        # Set flag to indicate the parameter change came from our controller
        self._parameter_value_changed_from_controller = True
        
        # Get the parameter (or skip if not found)
        if param_name not in self._param_refs:
            self.log_message(f"ERROR: Parameter {param_name} not found in references")
            return
            
        param = self._param_refs[param_name]
        
        # Check if we need to invert this parameter's value
        invert = False
        param_config = None
        
        if self._resolved_device_type in self._device_param_maps:
            device_param_map = self._device_param_maps[self._resolved_device_type]
            param_config = device_param_map.get(param_name)
            if param_config:
                invert = param_config.get('invert', False)
                if "Freq" in param_name:
                    self.log_message(f"*** PARAM INVERT: {param_name} has invert={invert}, config={param_config}")
        
        # Special handling for shape parameters (3-step toggle buttons) - Pro-Q 3 only
        if "Shape" in param_name and self._resolved_device_type == DEVICE_PRO_Q3:
            self._handle_shape_parameter(param_name, value, param)
            return
        
        # Check if this is a discrete parameter (is_quantized and has value_items)
        is_discrete = False
        try:
            is_discrete = hasattr(param, 'is_quantized') and param.is_quantized and hasattr(param, 'value_items')
        except Exception as e:
            self.log_message(f"Error checking if {param_name} is discrete: {str(e)}")
        
        if is_discrete:
            # Handle discrete parameter
            self._handle_discrete_parameter(param_name, value, param)
            return
        
        # All other parameters (including Q) are handled as continuous controls
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
            # For inverted parameters, we need to invert the direction
            if invert:
                change_direction = -change_direction
                self.log_message(f"INVERT: Inverting direction for {param_name} to {change_direction}")
            
            new_value = current_value + (change_direction * self.PARAMETER_STEP_SIZE)
            
            # Clamp to 0.0-1.0 range
            new_value = max(0.0, min(1.0, new_value))
            
            # Update our tracking value
            self._current_param_values[param_name] = new_value
            
            # Extra logging for Q parameters in Pro-Q 3
            if "Q" in param_name and self._resolved_device_type == "Pro-Q 3":
                self.log_message(f"Q PARAMETER RELATIVE: {param_name}, Dir: {change_direction}, New: {new_value:.3f}")
            
            # Log the change if debug is enabled
            invert_str = " (inverted)" if invert else ""
            self.debug_log(f"Encoder {param_name}{invert_str} - Direction: {change_direction}, " + 
                          f"Old value: {current_value:.3f}, New value: {new_value:.3f}")
        else:
            # ------ ABSOLUTE MODE ------
            # Store the MIDI value
            self._last_midi_values[param_name] = value
            
            # Scale the encoder value (0-127) to parameter range (0.0-1.0)
            # For inverted parameters, invert the MIDI value
            if invert:
                new_value = (127 - value) / 127.0
                self.log_message(f"*** INVERT APPLIED: {param_name} - Value inverted from {value} → {127-value}, resulting in {new_value:.3f}")
            else:
                new_value = value / 127.0
                if "Freq" in param_name and self._resolved_device_type == DEVICE_API_VISION:
                    self.log_message(f"*** NO INVERT: {param_name} - Value NOT inverted, using {value} → {new_value:.3f}")
            
            # Update our tracking value
            self._current_param_values[param_name] = new_value
            
            # Extra logging for Q parameters in Pro-Q 3
            if "Q" in param_name and self._resolved_device_type == DEVICE_PRO_Q3:
                self.log_message(f"Q PARAMETER ABSOLUTE: {param_name}, MIDI: {value}, New: {new_value:.3f}")
            
            # Log the change if debug is enabled
            invert_str = " (inverted)" if invert else ""
            self.debug_log(f"Encoder {param_name}{invert_str} - Absolute value: {value}, Param value: {new_value:.3f}")
        
        # Update the parameter in Live
        param.value = new_value
        
        # Extra verification for Q parameters in Pro-Q 3
        if "Q" in param_name and self._resolved_device_type == DEVICE_PRO_Q3:
            actual_value = param.value
            self.log_message(f"Q PARAMETER FINAL: {param_name}, Final value: {actual_value:.3f}")

    def _handle_discrete_parameter(self, param_name, value, param):
        """Handle discrete parameters with value_items"""
        # Get the invert flag for this parameter
        invert = False
        
        if self._resolved_device_type in self._device_param_maps:
            device_param_map = self._device_param_maps[self._resolved_device_type]
            param_config = device_param_map.get(param_name)
            if param_config:
                invert = param_config.get('invert', False)
        
        # Log the parameter being controlled
        num_values = len(param.value_items)
        self.log_message(f"DISCRETE PARAMETER: {param_name}, MIDI value: {value}, Items: {num_values}, Invert: {invert}")
        
        # Store the MIDI value
        self._last_midi_values[param_name] = value
        
        if self.EMULATE_RELATIVE_MODE:
            # ------ RELATIVE MODE ------
            # Get the current index
            current_index = int(param.value)
            
            # Determine the direction of movement
            change_direction = self._determine_relative_change(param_name, value)
            
            # Skip if no change detected
            if change_direction == 0:
                return
            
            # If inverted, reverse the direction
            if invert:
                change_direction = -change_direction
                self.log_message(f"*** DISCRETE INVERT: Reversing direction for {param_name} from {-change_direction} to {change_direction}")
                
            # Calculate the new index
            new_index = (current_index + change_direction) % num_values
            
            # Log the change
            invert_str = " (inverted)" if invert else ""
            self.log_message(f"DISCRETE REL{invert_str}: {param_name}, Current: {current_index} → New: {new_index} (of {num_values})")
            
            # Update the parameter with the new index
            param.value = new_index
        else:
            # ------ ABSOLUTE MODE ------
            # For inverted parameters, invert the MIDI value
            if invert:
                # Invert the value (0 becomes 127, 127 becomes 0)
                inverted_value = 127 - value
                self.log_message(f"*** DISCRETE INVERT: Inverting MIDI value for {param_name} from {value} to {inverted_value}")
                value = inverted_value
                
            # Map the MIDI value (0-127) to an index in the available values
            # This ensures we use the full range of the knob for all possible values
            index = min(int(value * num_values / 128), num_values - 1)
            
            # Log the mapped index
            invert_str = " (inverted)" if invert else ""
            self.log_message(f"DISCRETE ABS{invert_str}: {param_name}, MIDI: {value} → Index: {index} (of {num_values})")
            
            # Update the parameter in Live
            param.value = index
        
        # Store the current value (as the integer index)
        self._current_param_values[param_name] = param.value
            
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

    def _setup_device_listeners(self):
        """Setup device listeners for all tracks to detect when Pro-Q 3 is added"""
        try:
            # First remove any existing device listeners
            self._remove_device_listeners()
            
            # Add device listeners to all tracks
            for track in self.song().tracks:
                track.add_devices_listener(self._on_devices_changed)
                self.debug_log(f"Added device listener to track: {track.name}")
            
            # Also add to return tracks
            for track in self.song().return_tracks:
                track.add_devices_listener(self._on_devices_changed)
                self.debug_log(f"Added device listener to return track: {track.name}")
                
            # And master track
            self.song().master_track.add_devices_listener(self._on_devices_changed)
            self.debug_log("Added device listener to master track")
            
            self._has_device_listeners = True
            self.log_message("Device listeners set up on all tracks")
            
        except Exception as e:
            self.log_message("Error setting up device listeners:", str(e))

    def _remove_device_listeners(self):
        """Safely remove all device listeners"""
        try:
            if self._has_device_listeners:
                # Remove from all tracks
                for track in self.song().tracks:
                    try:
                        track.remove_devices_listener(self._on_devices_changed)
                    except:
                        pass  # Ignore errors if listener wasn't registered
                
                # Remove from return tracks
                for track in self.song().return_tracks:
                    try:
                        track.remove_devices_listener(self._on_devices_changed)
                    except:
                        pass
                    
                # Remove from master track
                try:
                    self.song().master_track.remove_devices_listener(self._on_devices_changed)
                except:
                    pass
                
                self._has_device_listeners = False
                self.debug_log("Removed all device listeners")
            
        except Exception as e:
            self.log_message("Error removing device listeners:", str(e))

    def _on_devices_changed(self):
        """Called when devices are added or removed from any track"""
        self.log_message("Devices changed on a track, checking for supported devices")
        
        # Check if our current device has been removed
        if self._resolved_device:
            # Get the track that had our device
            track = self._current_track
            
            # Check if our device still exists in the track's devices
            device_still_exists = False
            
            if track:
                # First check direct devices
                for device in track.devices:
                    if device == self._resolved_device or (hasattr(device, 'name') and device.name == self._resolved_device_type and self._resolved_device.name == self._resolved_device_type):
                        device_still_exists = True
                        break
                        
                # If not found directly, check rack devices recursively
                if not device_still_exists and track.devices:
                    for device in track.devices:
                        if hasattr(device, 'chains') and self._check_device_in_rack(device, self._resolved_device):
                            device_still_exists = True
                            break
            
            # If our device has been removed, clean up
            if not device_still_exists:
                device_type = self._resolved_device_type
                self.log_message(f"{device_type} device has been removed, cleaning up")
                self._remove_parameter_listeners()
                self._resolved_device = None
                self._resolved_device_type = None
                
                # Keep only the Volume parameter if it exists
                if "Volume" in self._param_refs:
                    volume_param = self._param_refs["Volume"]
                    self._param_refs = {"Volume": volume_param}
                else:
                    self._param_refs = {}
                    
                # Notify user
                self.log_message(f"{device_type} connection lost. Only track volume control remains active.")
        
        # If we don't have a device, schedule a search after a short delay
        # This gives the device time to fully initialize its parameters
        if not self._resolved_device:
            self.log_message("Scheduling device search with delay to allow parameters to initialize")
            self.schedule_message(2, self._delayed_device_search)  # ~100ms delay (2 ticks)

    def _check_device_in_rack(self, rack_device, target_device):
        """Recursively check if target_device exists in a rack device"""
        if not hasattr(rack_device, 'chains'):
            return False
        
        for chain in rack_device.chains:
            for device in chain.devices:
                # Direct match
                if device == target_device or (hasattr(device, 'name') and 
                                              device.name == target_device.name and 
                                              target_device.name in self.DEVICE_ORDER):
                    return True
                
                # Recursive check if this is a nested rack
                if hasattr(device, 'chains') and self._check_device_in_rack(device, target_device):
                    return True
                
        return False

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
        
        # Remove device listeners
        self._remove_device_listeners()
        
        # Remove track state listeners
        self._remove_track_state_listeners()
        
        # Remove track change listener
        try:
            if self._has_track_listener:
                self.song().view.remove_selected_track_listener(self._on_selected_track_changed)
                self._has_track_listener = False
        except Exception as e:
            self.log_message("Error removing track listener:", str(e))
            
        ControlSurface.disconnect(self)

    def _log_shape_mappings(self):
        """Log the shape, Q button and track control mappings for debugging purposes"""
        # Import for local use to avoid circular imports
        from .Console1_Hardware import SHAPE_SHELF, SHAPE_BELL, SHAPE_CUT, BUTTON_EQ_BYPASS
        
        self.log_message("------ Console1 Control Mappings ------")
        self.log_message("Supported Devices in Priority Order:")
        for i, device in enumerate(self.DEVICE_ORDER):
            self.log_message(f"{i+1}. {device}")
            
        # Log mappings for Pro-Q 3
        self.log_message("\nPro-Q 3 Mappings:")
        for param_name, config in self._proq3_cc_map.items():
            if param_name in ["Band 2 Shape", "Band 5 Shape", "Band 2 Q", "Band 5 Q", "Device On"]:
                cc_number = config['cc']
                invert = config.get('invert', False)
                invert_str = " (INVERTED)" if invert else ""
                self.log_message(f"- {param_name} -> CC {cc_number}{invert_str}")
                
        # Log mappings for API Vision
        self.log_message("\nAPI Vision Mappings:")
        for param_name, config in self._api_cc_map.items():
            cc_number = config['cc']
            invert = config.get('invert', False)
            invert_str = " (INVERTED)" if invert else ""
            self.log_message(f"- {param_name} -> CC {cc_number}{invert_str}")
            
        self.log_message("\nMIDI-to-ProQ3 Shape Mappings (Pro-Q 3 only):")
        self.log_message("Band 2:")
        self.log_message(f"- MIDI {SHAPE_SHELF} (Shelf) → ProQ3 1.0 (Low Shelf)")
        self.log_message(f"- MIDI {SHAPE_BELL} (Bell)  → ProQ3 0.0 (Bell)")
        self.log_message(f"- MIDI {SHAPE_CUT} (Cut)   → ProQ3 2.0 (Low Cut)")
        self.log_message("Band 5:")
        self.log_message(f"- MIDI {SHAPE_SHELF} (Shelf) → ProQ3 3.0 (High Shelf)")
        self.log_message(f"- MIDI {SHAPE_BELL} (Bell)  → ProQ3 0.0 (Bell)")
        self.log_message(f"- MIDI {SHAPE_CUT} (Cut)   → ProQ3 4.0 (High Cut)")
        
        # Q button mappings
        self.log_message("Q Control Mappings (Pro-Q 3 only):")
        self.log_message("- Using continuous mode for all Q parameters")
        
        # Bypass button mapping
        self.log_message("Bypass Button Mapping:")
        self.log_message(f"- CC {BUTTON_EQ_BYPASS} → Device On/Bypass")
        
        # Track control button mappings
        self.log_message("Track Control Button Mappings:")
        for control_name, cc_number in self._track_control_map.items():
            self.log_message(f"- CC {cc_number} → {control_name}")
        
        # Log mappings for Neve 1073
        self.log_message("\nNeve 1073 Mappings:")
        for param_name, config in self._neve_cc_map.items():
            cc_number = config['cc']
            invert = config.get('invert', False)
            invert_str = " (INVERTED)" if invert else ""
            self.log_message(f"- {param_name} -> CC {cc_number}{invert_str}")
            
        # Log which parameters have inversion enabled
        self.log_message("\nParameters with Inversion Enabled:")
        
        # Pro-Q 3 inverted parameters
        proq3_inverted = [param_name for param_name, config in self._proq3_cc_map.items() 
                         if config.get('invert', False)]
        if proq3_inverted:
            self.log_message("Pro-Q 3:")
            for param in proq3_inverted:
                self.log_message(f"- {param}")
        
        # API Vision inverted parameters
        api_inverted = [param_name for param_name, config in self._api_cc_map.items() 
                       if config.get('invert', False)]
        if api_inverted:
            self.log_message("API Vision:")
            for param in api_inverted:
                self.log_message(f"- {param}")
                
        # Neve 1073 inverted parameters
        neve_inverted = [param_name for param_name, config in self._neve_cc_map.items() 
                        if config.get('invert', False)]
        if neve_inverted:
            self.log_message("Neve 1073:")
            for param in neve_inverted:
                self.log_message(f"- {param}")
        
        if not proq3_inverted and not api_inverted and not neve_inverted:
            self.log_message("No parameters have inversion enabled")
        
        self.log_message("-----------------------------------")

    def _delayed_device_search(self):
        """Search for supported devices with a delay to allow parameters to initialize"""
        self.log_message("Running delayed device search")
        found = self._find_device_on_any_track()
        
        # If still not found, try again with a longer delay
        if not found:
            self.log_message("No supported devices found, scheduling another search with longer delay")
            self.schedule_message(10, self._final_device_search)  # ~500ms delay (10 ticks)

    def _final_device_search(self):
        """Final attempt to find supported devices after allowing time for initialization"""
        self.log_message("Running final device search")
        found = self._find_device_on_any_track()
        
        if not found:
            self.log_message("No supported devices found after multiple attempts")
        else:
            self.log_message(f"Found {self._resolved_device_type} after delayed search")