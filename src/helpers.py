"""
Defining basic data generating function and setting variables

"""

import datetime
import pandas as pd
from meteostat import Point, Daily
import config as cg

cities = {
    "Warszawa": (52.2297, 21.0122),
    "Kraków": (50.0647, 19.9450),
    "Łódź": (51.7592, 19.4550),
    "Wrocław": (51.1079, 17.0385),
    "Poznań": (52.4064, 16.9252),
    "Gdańsk": (54.3520, 18.6466),
    "Szczecin": (53.4285, 14.5528),
    "Bydgoszcz": (53.1235, 18.0084),
    "Lublin": (51.2465, 22.5684),
    "Białystok": (53.1325, 23.1688),
    "Katowice": (50.2649, 19.0238),
    "Gorzów Wielkopolski": (52.7368, 15.2288),
    "Zielona Góra": (51.9355, 15.5062),
    "Rzeszów": (50.0412, 21.9991),
    "Kielce": (50.8661, 20.6286),
    "Olsztyn": (53.7767, 20.4752),
    "Opole": (50.6751, 17.9213),
}

DATE_RANGE = 30

TAVG_HEIGHT = 1000
WSPD_HEIGHT = 250
PRES_HEIGHT = 250
PRCP_HEIGHT = 500


def get_data(delta: int):
    """
    Fetches data for cities in config, looking secified amount days back.

    :param delta: Number of days to look back
    :return: DataFrame with basic weather statistics for all the cities and dates
    """
    start = datetime.datetime.today() - datetime.timedelta(days=delta)
    end = datetime.datetime.today()

    all_data = []

    for city, (lat, lon) in cg.cities.items():
        location = Point(lat, lon)

        data_tmp = Daily(location, start, end)
        data_tmp = data_tmp.fetch()

        data_tmp["City"] = city

        data_tmp.reset_index(inplace=True)
        all_data.append(data_tmp)
    data_complete = pd.concat(all_data, ignore_index=True)

    return data_complete


if __name__ == "__main__":
    data = get_data(30)
    print(data)
