import Live
from .Console1DeviceControl import Console1DeviceControl


def create_instance(c_instance):
    """ Creates and returns the Console1DeviceControl controller script """
    return Console1DeviceControl(c_instance)

# local variables:
# tab-width: 4