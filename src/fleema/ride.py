import datetime
import warnings

import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fleema.vehicle import VehicleType
    from fleema.location import Location


class RideCalc:
    def __init__(
        self,
        consumption_table: pd.DataFrame,
        distances: pd.DataFrame,
        inclines: pd.DataFrame,
        temperature: pd.DataFrame,
        temperature_option,
        defaults: dict,
    ) -> None:
        """RideCalc constructor.

        Parameters
        ----------
        consumption_table : DataFrame
            DataFrame containing consumption by vehicle type, speed, etc.
        distances : DataFrame
            Distance matrix between all Locations
        inclines : DataFrame
            Incline matrix between all Locations
        temperature : Dataframe
            Highest, lowest and median temperature for a day
        temperature_option : str
            Contains string of column that is used in temperature dataframe.
        defaults : dict
            Contains default values for the inputs in the consumption calculation.
        """
        self.consumption_table = consumption_table
        self.distances = distances
        self.inclines = inclines
        self.temperature = temperature
        self.temperature_option = temperature_option
        self.defaults = defaults
        if self.defaults["speed"] <= 0:
            raise ValueError("Speed can not be smaller or equal to zero.")

        self.uniques = [
            sorted(self.consumption_table[col].unique())
            for col in self.consumption_table.iloc[:, :-1]
        ]

    def calculate_trip(
        self,
        origin: "Location",
        destination: "Location",
        vehicle_type: "VehicleType",
        speed: float,
        departure_time: str = "2022-01-01 01:01:00",
        level_of_loading: float = 0,
    ):
        """Calculate consumption as a part of total SoC.

        Parameters
        ----------
        origin : Location
            Starting location of trip
        destination : Location
            Ending location of trip
        vehicle_type : VehicleType
            Vehicle type to look up in consumption and for calculation of SoC
        speed : float
            Average speed during the given trip.
        departure_time : str
            Departure time represented by a string.
        level_of_loading : float
            Number between 0 and 1 that represents the occupation of the vehicle capacity.
            Default is zero.

        Returns
        -------
        dict[float, float, float]
            Returns dict with the keys "consumption", "soc_delta", "trip_time"

        """
        temperature = self.get_temperature(departure_time)
        distance, incline = self.get_location_values(origin, destination)
        if speed <= 0:
            warnings.warn(
                f"Bad option: Speed is smaller than or equal to zero. Default is set to {self.defaults['speed']}"
            )
            speed = self.defaults["speed"]
        if distance == 0:
            return {
                "consumption": 0,
                "soc_delta": 0,
                "trip_time": 0,
            }
        trip_time = max(distance / speed * 60, 1)
        consumption, soc_delta = self.calculate_consumption(
            vehicle_type, incline, temperature, speed, level_of_loading, distance
        )

        return {
            "consumption": consumption,
            "soc_delta": soc_delta,
            "trip_time": trip_time,
        }

    def calculate_consumption(
        self,
        vehicle_type: "VehicleType",
        incline,
        temperature,
        speed,
        level_of_loading,
        distance,
    ):
        """Calculates the reduction in SoC of a vehicle type when driving the specified route.

        Parameters
        ----------
        vehicle_type : VehicleType
            Vehicle type to look up in consumption and for calculation of SoC
        incline : float
            Average incline of trip
        temperature : float
            Ambient temperature
        speed : float
            Average speed during trip
        level_of_loading : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle
        distance : float
            Distance of trip in km

        Returns
        -------
        tuple[float, float]
            Returns consumption in kWh and the SoC delta resulting from this trip

        """
        consumption_factor = self.get_consumption(
            vehicle_type.name, level_of_loading, incline, temperature, speed
        )
        if distance < 0:
            raise ValueError("Distance is smaller than zero.")
        consumption = consumption_factor * distance

        return consumption, consumption / vehicle_type.battery_capacity

    def get_consumption(
        self,
        vehicle_type_name: str,
        level_of_loading,
        incline,
        temperature,
        speed,
    ):
        """Get consumption in kWh/km for a specified vehicle type and route.

        Parameters
        ----------
        vehicle_type_name : str
            Vehicle type name to look up in consumption table
        incline : float
            Average incline of trip
        temperature : float
            Ambient temperature
        speed : float
            Average speed during trip
        level_of_loading : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle

        Returns
        -------
        float
            Returns consumption factor in kWh/km

        """
        (
            level_of_loading,
            incline,
            temperature,
            speed,
        ) = self._validate_consumption_inputs_and_get_defaults(
            level_of_loading, incline, temperature, speed
        )

        df = self.consumption_table[
            self.consumption_table["vehicle_type"] == vehicle_type_name
        ]

        inc_col = df["incline"]
        tmp_col = df["t_amb"]
        lol_col = df["level_of_loading"]
        speed_col = df["mean_speed"]
        cons_col = df["consumption"]
        data_table = list(zip(lol_col, inc_col, speed_col, tmp_col, cons_col))

        consumption_value = self.nd_interp(
            (level_of_loading, incline, speed, temperature), data_table
        )

        return consumption_value * (-1)

    def nd_interp(self, input_values, lookup_table):
        """Interpolate value from multiple input values and a lookup table

        Parameters
        ----------
        input_values : tuple
            Tuple of one value for each but the last column of the lookup table, in order
        lookup_table : list
            Lookup table as a matrix

        Returns
        -------
        float
            Return interpolated value from last column

        """
        # find nearest value(s) per column
        lower = [None] * len(input_values)
        upper = [None] * len(input_values)
        for i, v in enumerate(input_values):
            # initialize for out of bound values -> Constant value since lower and upper will both
            # be the same boundary value. Still allows for interpolation in other dimensions
            # forcing lower<upper could be implemented for extrapolation beyond the bounds.
            lower[i], upper[i] = self.get_nearest_uniques(v, i + 1)  # type: ignore
        # find rows in table made up of only lower or upper values
        points = []
        for row in lookup_table:
            for i, v in enumerate(row[:-1]):
                if lower[i] != v and upper[i] != v:
                    break
            else:
                points.append(row)

        # interpolate between points that differ only in current dimension
        for i, x in enumerate(input_values):
            new_points = []
            # find points that differ in just that dimension
            for j, p1 in enumerate(points):
                for p2 in points[j + 1 :]:
                    for k in range(len(input_values)):
                        if p1[k] != p2[k] and i != k:
                            break
                    else:
                        # differing row found
                        x1 = p1[i]
                        y1 = p1[-1]
                        x2 = p2[i]
                        y2 = p2[-1]
                        dx = x2 - x1
                        dy = y2 - y1
                        m = dy / dx
                        n = y1 - m * x1
                        y = m * x + n
                        # generate new point at interpolation
                        p = [v for v in p1]
                        p[i] = x
                        p[-1] = y
                        new_points.append(p)
                        # only couple
                        break
                else:
                    # no matching row (singleton dimension?)
                    new_points.append(p1)
            points = new_points

        return points[0][-1]

    def get_nearest_uniques(self, value: float, column):
        """Returns the nearest upper and lower consumption input for a specified value and a column name.

        Parameters
        ----------
        value : float
            Value of the parameter matching with the column
        column : int
            Number of the column in self.consumption

        Returns
        -------
        tuple[float, float]
            Returns lower and upper unqiue boundary surrounding the input value (may be the same number twice)

        """
        # give upper and lower default maximum values, in case no upper bound gets found
        upper = self.uniques[column][-1]
        lower = self.uniques[column][0]
        # check if the value is exactly one of the uniques
        if value in self.uniques[column]:
            upper = value
            lower = value
        elif value > upper:
            lower = upper
        else:
            # find the first unique thats bigger than the value (uniques is sorted)
            for count, bound in enumerate(self.uniques[column]):
                if bound > value:
                    upper = bound
                    lower = self.uniques[column][count - 1] if count > 0 else bound
                    break

        return lower, upper

    def get_location_values(self, origin: "Location", destination: "Location"):
        """Get distance and incline between two locations, on the trip from origin to destination.

        Parameters
        ----------
        origin : Location
            Starting location of trip
        destination : Location
            Ending location of trip

        Returns
        -------
        tuple[float, float]
            Returns distance and incline between the locations

        """
        distance = self.distances.at[origin.name, destination.name]
        incline = self.inclines.at[origin.name, destination.name]

        return distance, incline

    def get_temperature(self, departure_time):
        """Returns temperature according to the given time parameter.

        Parameters
        ----------
        departure_time : str
            Departure time represented by a string.

        Warnings
        --------
        bad csv format
            Example column structure: hour | <optional_name> | ...
            If csv has wrong format method returns 20 degrees.
        bad temperature option
            If column does not exist temperature.csv option will be set to first column.
        bad format
            Parameter allows following format: '%Y-%m-%d %H:%M:%S'. Example: '2022-01-01 01:01:00'
            Sets departure_time to '2022-01-01 12:00:00'.

        Returns
        -------
        float
            temperature
        """
        if self.temperature.columns[0] != "hour" or len(self.temperature.columns) < 2:
            warnings.warn(
                "Bad csv format: Columns should be structured and named like this: "
                "hour | <optional_name> | ... "
                "Returns temperature of 20 degrees."
            )
            return 20.0
        if self.temperature_option not in self.temperature.columns:
            warnings.warn(
                f"Bad temperature option: The column {self.temperature_option} "
                "does not exist in temperature.csv. "
                "Option default is set to the second column in temperature.csv."
            )
            self.temperature_option = self.temperature.columns[1]
        # check departure time format
        try:
            datetime.datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            warnings.warn(
                "Bad format: Wrong datetime string format. Example: '2022-01-01 01:01:00'"
            )
            departure_time = "2022-01-01 12:00:00"
        step = datetime.datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S").hour
        row = self.temperature.loc[self.temperature["hour"] == step]
        return row[self.temperature_option].values[0]

    def _validate_consumption_inputs_and_get_defaults(
        self, level_of_loading, incline, temperature, speed
    ):
        """Returns validated inputs with respective defaults if needed.

        Parameters
        ----------
        level_of_loading : float
        incline: float
        temperature : float
        speed : float

        Returns
        -------
        float, float, float, float
        level_of_loading, incline, temperature, speed
        """
        defaults = {
            "level_of_loading": level_of_loading,
            "incline": incline,
            "temperature": temperature,
            "speed": speed,
        }

        # level_of_loading
        if not 0 <= defaults["level_of_loading"] <= 1:
            warnings.warn(
                f"Bad option: Load level is not between 0 and 1. Default is set to {self.defaults['level_of_loading']}."
            )
            defaults["level_of_loading"] = self.defaults["level_of_loading"]

        # speed
        if defaults["speed"] < 0:
            warnings.warn(
                f"Bad option: Speed is smaller than 0. Default is set to {self.defaults['speed']}."
            )
            defaults["speed"] = self.defaults["speed"]

        return tuple(defaults.values())
