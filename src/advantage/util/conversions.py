import datetime


def step_to_timestamp(time_series, time_step):
    """This function returns the timestamp of the respective step in the time series

    Parameters
    ----------
    time_series : 'pandas.core.indexes.datetimes.DatetimeIndex
        Series of timestamps to look up from.
    time_step : int
        Relevant time step of the simulation.

    Returns
    -------
    datetime.DateTime
        Timestamp that is looked up in the time series.

    """
    return time_series[int(time_step)]


def date_string_to_datetime(date_str):
    """This function converts a string of a date into a datetime.date object.

    Parameter
    ---------
    date_str : str
        String object of a specific date with format YYYY-mm-dd. Example: 2021-7-5

    Returns
    -------
    datetime.date
        Datetime.date object of date_str with format YYYY-mm-dd. Example: 2021-07-05

    """
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")


def datetime_string_to_datetime(date_str):
    """This function converts a string of a date into a datetime.date object.

    Parameter
    ---------
    date_str : str
        String object of a specific date with format YYYY-mm-dd HH:MM:SS. Example: 2021-07-05 07:42:00

    Returns
    -------
    datetime.date
        Datetime.date object of date_str with format YYYY-mm-dd HH:MM:SS. Example: 2021-07-05 07:42:00

    """
    date_str = date_str.strip()
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
