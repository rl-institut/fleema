import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from advantage.vehicle import VehicleType
    from advantage.location import Location


class RideCalc:
    def __init__(self, consumption_table: pd.DataFrame, distances: pd.DataFrame, inclines: pd.DataFrame) -> None:
        self.consumption_table = consumption_table
        self.distances = distances
        self.inclines = inclines

        self.uniques = {
            col: sorted(self.consumption_table[col].unique()) for col in self.consumption_table.iloc[:, :-1]
            }

    # TODO 6. write interpolation, based on find_rows and its input values
    # TODO 5. create RideCalc in Simulation and use it in decisionmaking / point evaluation / ...

    def calculate_trip(self, origin: "Location", destination: "Location", vehicle_type: "VehicleType", temperature):
        # TODO add speed as scenario input, load level somewhere?
        speed = 8.65
        load_level = 0
        distance, incline = self.get_location_values(origin, destination)

        return self.calculate_consumption(vehicle_type, incline, temperature, speed, load_level, distance)

    def calculate_consumption(self, vehicle_type: "VehicleType", incline, temperature, speed, load_level, distance):
        """Calculates the reduction in SoC of a vehicle type when driving the specified route."""
        consumption_factor = self.get_consumption(vehicle_type.name, incline, temperature, speed, load_level)
        consumption = consumption_factor * distance

        return consumption * vehicle_type.battery_capacity / 100

    def get_consumption(self, vehicle_type_name: str, incline, temperature, speed, load_level):
        """
        """

        filtered = self.consumption_table.loc[self.consumption_table["vehicle_type"] == vehicle_type_name]

        # TODO maybe solve via **kwargs and a loop?
        incline_lower, incline_upper = self.get_nearest_uniques(incline, "incline")
        filtered = filtered.loc[filtered["incline"].between(incline_lower, incline_upper)]

        temp_lower, temp_upper = self.get_nearest_uniques(temperature, "t_amb")
        filtered = filtered.loc[filtered["t_amb"].between(temp_lower, temp_upper)]

        sp_lower, sp_upper = self.get_nearest_uniques(speed, "sp_type")
        filtered = filtered.loc[filtered["sp_type"].between(sp_lower, sp_upper)]

        load_lower, load_upper = self.get_nearest_uniques(load_level, "level_of_loading")
        filtered = filtered.loc[filtered["level_of_loading"].between(load_lower, load_upper)]

        # TODO add interpolation here to get correct value
        consumption_value = filtered["consumption"].mean()

        return consumption_value

    def get_nearest_uniques(self, value: float, column):
        """Returns the nearest upper and lower consumption input for a specified value and a column name.

        Parameters
        ----------
        value : float
            Value of the parameter matching with the column
        column : ?
            Name of the column in self.consumption

        Returns
        -------
        float, float
            Returns lower and upper unqiue boundary surrounding the input value (may be the same number twice)

        """
        # give upper and lower default maximum values, in case no upper bound gets found
        upper = self.uniques[column][-1]
        lower = self.uniques[column][-1]
        # check if the value is exactly one of the uniques
        if value in self.uniques[column]:
            upper = value
            lower = value
        else:
            # find the first unique thats bigger than the value (uniques is sorted)
            for count, bound in enumerate(self.uniques[column]):
                if bound > value:
                    upper = bound
                    lower = self.uniques[column][count-1] if count > 0 else bound
                    break

        return lower, upper

    def get_location_values(self, origin: "Location", destination: "Location"):
        """Takes two locations as input and returns distance and incline between them."""
        distance = self.distances.at[origin.name, destination.name]
        incline = self.inclines.at[origin.name, destination.name]

        return distance, incline


# TODO remove  / convert to test script
if __name__ == "__main__":
    import pathlib
    cons_path = pathlib.Path("scenarios", "public_transport_base", "consumption.csv")
    cons = pd.read_csv(cons_path)
    rc = RideCalc(cons, cons, cons)
    print(rc.uniques)
    print(rc.get_consumption("bus_18m", 0.01, 1., 8.65, 0.))
