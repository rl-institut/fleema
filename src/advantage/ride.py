import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from advantage.vehicle import VehicleType
    from advantage.location import Location


class RideCalc:
    def __init__(
        self,
        consumption_table: pd.DataFrame,
        distances: pd.DataFrame,
        inclines: pd.DataFrame,
    ) -> None:
        self.consumption_table = consumption_table
        self.distances = distances
        self.inclines = inclines

        self.uniques = [
            sorted(self.consumption_table[col].unique())
            for col in self.consumption_table.iloc[:, :-1]
        ]

    def calculate_trip(
        self,
        origin: "Location",
        destination: "Location",
        vehicle_type: "VehicleType",
        temperature: float,
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
        temperature : float
            Ambient temperature

        Returns
        -------
        tuple[float, float]
            Returns conusmption in kWh and the SoC delta resulting from this trip

        """
        # TODO add speed as scenario input, load level somewhere?
        speed = 8.65
        load_level = 0
        distance, incline = self.get_location_values(origin, destination)

        return self.calculate_consumption(
            vehicle_type, incline, temperature, speed, load_level, distance
        )

    def calculate_consumption(
        self,
        vehicle_type: "VehicleType",
        incline,
        temperature,
        speed,
        load_level,
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
        load_level : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle
        distance : float
            Distance of trip in km

        Returns
        -------
        tuple[float, float]
            Returns conusmption in kWh and the SoC delta resulting from this trip

        """
        consumption_factor = self.get_consumption(
            vehicle_type.name, incline, temperature, speed, load_level
        )
        consumption = consumption_factor * distance

        return consumption, consumption / vehicle_type.battery_capacity

    def get_consumption(
        self, vehicle_type_name: str, incline, temperature, speed, load_level
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
        load_level : float
            Level of load from 0 - 1, 1 being the maximum load of the vehicle

        Returns
        -------
        float
            Returns consumption faktor in kWh/km

        """

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
            (load_level, incline, speed, temperature), data_table
        )

        return consumption_value

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
