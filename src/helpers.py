import datetime
from meteostat import Point, Daily
from config import *
import pandas as pd


def get_data(delta: int):
    start = datetime.datetime.today() - datetime.timedelta(days=delta)
    end = datetime.datetime.today()

    all_data = []

    # Iteracja po miastach
    for city, (lat, lon) in cities.items():
        location = Point(lat, lon)

        data = Daily(location, start, end)
        data = data.fetch()

        data["City"] = city

        data.reset_index(inplace=True)
        all_data.append(data)

    # Łączenie wszystkich danych w jeden DataFrame
    data_complete = pd.concat(all_data, ignore_index=True)

    return data_complete


if __name__ == "__main__":
    data = get_data(30)
    data2 = (
        data.groupby("time")
        .agg({"tavg": "mean", "wspd": "mean", "pres": "mean", "prcp": "sum"})
        .reset_index()
    )
    print(data2)
