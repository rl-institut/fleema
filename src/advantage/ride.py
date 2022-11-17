import pandas as pd

class RideCalc:
    def __init__(self, consumption_table: pd.DataFrame, distances, inclines) -> None:
        self.consumption_table = consumption_table
        self.distances = distances
        self.inclines = inclines

        self.uniques = {col:sorted(self.consumption_table[col].unique()) for col in self.consumption_table.iloc[:,:-1]}

    def find_rows(self, bus_type, incline, temperature, sp_type, load_level):
        """"""

        filtered = self.consumption_table.loc[self.consumption_table["bus_type"] == bus_type]    

        # TODO maybe solve via **kwargs and a loop?
        incline_lower, incline_upper = self.get_nearest_uniques(incline, "incline")
        filtered = filtered.loc[filtered["incline"].between(incline_lower, incline_upper)]
        
        temp_lower, temp_upper = self.get_nearest_uniques(temperature, "t_amb")
        filtered = filtered.loc[filtered["t_amb"].between(temp_lower, temp_upper)]

        sp_lower, sp_upper = self.get_nearest_uniques(sp_type, "sp_type")
        filtered = filtered.loc[filtered["sp_type"].between(sp_lower, sp_upper)]

        load_lower, load_upper = self.get_nearest_uniques(load_level, "level_of_loading")
        filtered = filtered.loc[filtered["level_of_loading"].between(load_lower, load_upper)]

        return filtered

    def get_nearest_uniques(self, value:float, column):
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

if __name__ == "__main__":
    import pathlib
    cons_path = pathlib.Path("scenarios", "public_transport_base", "consumption.csv")
    cons = pd.read_csv(cons_path)
    rc = RideCalc(cons, None, None)
    print(rc.uniques)
    print(rc.find_rows("bus_18m", 0.01, 1., 8.65, 0.))

# def interpolate_consumption(self, incline, temperature, distance, sp_type=8.65, level_of_loading=0.):
#         # extract possible rows from consumption_df
#         # find the 2 points to interpolate

#         rows = self.consumption['incline']

#         # reductions
#         rows = self._nearest_rows(rows, incline)
#         rows = self._nearest_rows(rows, temperature)
#         rows = self._nearest_rows(rows, distance)
#         rows = self._nearest_rows(rows, sp_type)
#         rows = self._nearest_rows(rows, level_of_loading)

#         # real interpolation between the rows which remain
#         consumption_index = 0

#         return self.consumption['consumption'][consumption_index]

# def _nearest_rows(self, rows, param):
#     from decimal import Decimal
#     return_rows = None
#     rows_values = rows.tolist()
#     # if param has an exact value like in the consumption table
#     if param in rows_values:
#         return rows.loc[lambda x: x == param]

#     #smallest_gap_minus = math.inf
#     #smallest_gap_plus = math.inf
#     for i in range(len(rows_values)):
#         if rows_values[i] < param:
#             gap_minus = param - rows_values[i]
#             if gap_minus < smallest_gap_minus:
#                 smallest_gap_minus = round(gap_minus, 2)
#         if rows_values[i] > param:
#             gap_plus = float(rows_values[i] - param)
#             if gap_plus < smallest_gap_plus:
#                 smallest_gap_plus = round(gap_plus, 2)

#     minus_value = round(param + smallest_gap_minus*.1, 2)
#     plus_value = round(param + smallest_gap_plus, 2)
#     row_minus = rows.loc[lambda x: x == minus_value]
#     row_plus = rows.loc[lambda x: x == plus_value]

#     print(minus_value)
#     print(plus_value)
#     print()
#     print(row_minus)
#     print(row_plus)

#     print(rows.to_string())


#     return return_rows
