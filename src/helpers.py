"""
Defining basic data generating function

"""

import datetime
from meteostat import Point, Daily
from config import *
import pandas as pd


def get_data(delta: int):
    """
    Fetches data for cities in config, looking secified amount days back.

    :param delta: Number of days to look back
    :return: DataFrame with basic weather statistics for all the cities and dates
    """
    start = datetime.datetime.today() - datetime.timedelta(days=delta)
    end = datetime.datetime.today()

    all_data = []

    for city, (lat, lon) in cities.items():
        location = Point(lat, lon)

        data = Daily(location, start, end)
        data = data.fetch()

        data["City"] = city

        data.reset_index(inplace=True)
        all_data.append(data)
    data_complete = pd.concat(all_data, ignore_index=True)

    return data_complete


if __name__ == "__main__":
    data = get_data(30)
    print(data)
