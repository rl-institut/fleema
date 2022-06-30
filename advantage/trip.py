
class Trip:

    def __init__(self, vehicle, time_step):
        self.destination = ""
        self.distance = 0
        self.park_start = time_step
        self.park_time = 0
        self.drive_start = 0
        self.drive_time = 0
        self.park_timestamp = None
        self.drive_timestamp = None
        self.location = vehicle.status
        self.vehicle = vehicle
