from __future__ import with_statement

import Live
from _Framework.ControlSurface import ControlSurface


class Console1Controller(ControlSurface):
    __doc__ = " Stripped down Console1Controller script that does nothing "

    _active_instances = []

    def _combine_active_instances():
        pass
    _combine_active_instances = staticmethod(_combine_active_instances)

    def __init__(self, c_instance):
        ControlSurface.__init__(self, c_instance)
        # Initialize a completely stripped down controller that does nothing
        self.log_message("Console1Controller: Loaded successfully!")
        with self.component_guard():
            pass

    def disconnect(self):
        ControlSurface.disconnect(self)