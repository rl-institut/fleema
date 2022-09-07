import datetime


def step_to_timestamp(time_series, time_step):
    return time_series[time_step]


def date_string_to_datetime(date_str):
    date_str = date_str.split("-")
    return datetime.date(int(date_str[0]), int(date_str[1]), int(date_str[2]))
