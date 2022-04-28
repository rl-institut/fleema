from dataclasses import dataclass
import location


@dataclass
class Vehicle:
    """
    The vehicle contains tech parameters as well as tasks.
    Functions:
        charge
        drive
    """
    type: str
    status: str
    soc: float
    availability: bool
    rotation: str = None
    current_location: location.Location = None
    output = None
    task = None

    def charge(self):
        # call spiceev charging depending on soc, location, task
        return

    def drive(self):
        # call drive api with task, soc, ...
        return
