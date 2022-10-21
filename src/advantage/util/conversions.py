import datetime


def step_to_timestamp(time_series, time_step):
    return time_series[time_step]


def date_string_to_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d")


def datetime_string_to_datetime(date_str):
    # 2022-07-05 07:42:00
    date_str = date_str.strip()
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
