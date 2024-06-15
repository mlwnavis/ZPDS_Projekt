"""
Core application

"""

import os
import datetime
import pandas as pd  # type: ignore
from dash import Dash, html, dcc  # type: ignore
from dash.dependencies import Input, Output  # type: ignore
from flask_caching import Cache  # type: ignore
import plotly.express as px  # type: ignore

# import helpers as hp # type: ignore
from meteostat import Point, Daily

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

    for city, (lat, lon) in cities.items():
        location = Point(lat, lon)

        data_tmp = Daily(location, start, end)
        data_tmp = data_tmp.fetch()

        data_tmp["City"] = city

        data_tmp.reset_index(inplace=True)
        all_data.append(data_tmp)
    data_complete = pd.concat(all_data, ignore_index=True)

    return data_complete


app = Dash(__name__, assets_folder="../assets")

server = app.server


CACHE_CONFIG = {
    # try 'FileSystemCache' if you don't want to setup redis
    "CACHE_TYPE": "redis",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

# Data source
df = get_data(DATE_RANGE)

# App layout
app.layout = html.Div(
    [
        html.H1(children="Historia pogody"),
        html.Div(
            children="""
            Aplikacja napisana w Dashu
        """
        ),
        html.Div(
            [
                html.H3(children="Miasto", className="card"),
                dcc.Dropdown(
                    options=[
                        {"label": city, "value": city} for city in df["City"].unique()
                    ]
                    + [
                        {"label": "Wszystkie", "value": "Wszystkie"},
                        {"label": "Cała Polska", "value": "Cała Polska"},
                    ],
                    value="Poznań",
                    id="city-selection",
                    multi=False,
                ),
            ]
        ),
        html.Div(
            [
                html.H3(children="Zakres dni", className="card"),
                dcc.Slider(
                    id="days-range",
                    min=1,
                    max=30,
                    step=1,
                    value=30,
                    marks={i: str(i) for i in range(1, DATE_RANGE + 1)},
                ),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Loading(
                            id="loading-pres",
                            type="default",
                            children=html.Div(
                                id="pres-charts-container",
                                style={
                                    "height": f"{PRES_HEIGHT}px",
                                    "overflowY": "scroll",
                                },
                            ),
                        ),
                        dcc.Loading(
                            id="loading-wspd",
                            type="default",
                            children=html.Div(
                                id="wspd-charts-container",
                                style={
                                    "height": f"{WSPD_HEIGHT}px",
                                    "overflowY": "scroll",
                                },
                            ),
                        ),
                        dcc.Loading(
                            id="loading-prcp",
                            type="default",
                            children=html.Div(
                                id="prcp-charts-container",
                                style={
                                    "height": f"{PRCP_HEIGHT}px",
                                    "overflowY": "scroll",
                                },
                            ),
                        ),
                    ],
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "vertical-align": "top",
                    },
                ),
                html.Div(
                    [
                        dcc.Loading(
                            id="loading-tavg",
                            type="default",
                            children=html.Div(
                                id="tavg-charts-container",
                                style={
                                    "height": f"{TAVG_HEIGHT}px",
                                    "overflowY": "scroll",
                                },
                            ),
                        ),
                    ],
                    style={
                        "width": "50%",
                        "display": "inline-block",
                        "vertical-align": "top",
                    },
                ),
            ],
            style={"display": "flex"},
        ),
        dcc.Store(id="signal"),
    ]
)


@cache.memoize()
def global_store(city, days):
    """
    Fetches and processes the data for the selected city and days range.

    :param city: Selected city, 'Wszystkie' for all cities, or 'Cała Polska' for average statistics
    :param days: Number of days to look back
    :return: Filtered DataFrame for the selected city and days range
    """
    if city == "Wszystkie":
        return filter_city_days(df, None, days)
    if city == "Cała Polska":
        return (
            filter_city_days(df, None, days)
            .groupby("time")
            .agg({"tavg": "mean", "wspd": "mean", "pres": "mean", "prcp": "sum"})
            .reset_index()
        )

    return filter_city_days(df, city, days)


@app.callback(
    [
        Output("tavg-charts-container", "children"),
        Output("wspd-charts-container", "children"),
        Output("pres-charts-container", "children"),
        Output("prcp-charts-container", "children"),
    ],
    Input("signal", "data"),
)
def update_graph(value):
    """
    Updates the plots according to the selected city and days range.

    :param value: Selected city and days value from dcc.Store
    :return: Updated plotly figures
    """
    df_preprocessed = global_store(value["City"], value["Days"])
    city = value["City"]
    days = value["Days"]

    if city == "Wszystkie":
        cities_processed = df_preprocessed["City"].unique()
        tavg_graphs = []
        wspd_graphs = []
        pres_graphs = []
        prcp_graphs = []
        for city in cities_processed:
            city_data = df_preprocessed[df_preprocessed["City"] == city]
            tavg_fig = px.line(
                city_data,
                x="time",
                y="tavg",
                title=f"Średnia temperatura dla {city} w ostatnich {days} dniach",
                height=TAVG_HEIGHT,
                labels={"time": "Dzień", "tavg": "°C"},
            )
            wspd_fig = px.line(
                city_data,
                x="time",
                y="wspd",
                title=f"Średnia prędkość wiatru w {city} w ostatnich {days} dniach",
                height=WSPD_HEIGHT,
                labels={"time": "Dzień", "wspd": "km/h"},
            )
            pres_fig = px.line(
                city_data,
                x="time",
                y="pres",
                title=f"Średnie ciśnienie atmosferyczne w {city} w ostatnich {days} dniach",
                height=PRES_HEIGHT,
                labels={"time": "Dzień", "pres": "hPa"},
            )
            prcp_fig = px.bar(
                city_data,
                x="time",
                y="prcp",
                title=f"Opady atmosferyczne w {city} w ostatnich {days} dniach",
                height=PRCP_HEIGHT,
                labels={"time": "Dzień", "prcp": "mm"},
            )

            tavg_graphs.append(
                html.Div(dcc.Graph(figure=tavg_fig), style={"margin-bottom": "50px"})
            )
            wspd_graphs.append(
                html.Div(dcc.Graph(figure=wspd_fig), style={"margin-bottom": "50px"})
            )
            pres_graphs.append(
                html.Div(dcc.Graph(figure=pres_fig), style={"margin-bottom": "50px"})
            )
            prcp_graphs.append(
                html.Div(dcc.Graph(figure=prcp_fig), style={"margin-bottom": "50px"})
            )
        return tavg_graphs, wspd_graphs, pres_graphs, prcp_graphs
    if city == "Cała Polska":
        tavg_fig = px.line(
            df_preprocessed,
            x="time",
            y="tavg",
            title=f"Średnia temperatura dla {city} w ostatnich {days} dniach",
            height=TAVG_HEIGHT,
            labels={"time": "Dzień", "tavg": "°C"},
        )
        wspd_fig = px.line(
            df_preprocessed,
            x="time",
            y="wspd",
            title=f"Średnia prędkość wiatru w {city} w ostatnich {days} dniach",
            height=WSPD_HEIGHT,
            labels={"time": "Dzień", "wspd": "km/h"},
        )
        pres_fig = px.line(
            df_preprocessed,
            x="time",
            y="pres",
            title=f"Średnie ciśnienie atmosferyczne w {city} w ostatnich {days} dniach",
            height=PRES_HEIGHT,
            labels={"time": "Dzień", "pres": "hPa"},
        )
        prcp_fig = px.bar(
            df_preprocessed,
            x="time",
            y="prcp",
            title=f"Opady atmosferyczne w {city} w ostatnich {days} dniach",
            height=PRCP_HEIGHT,
            labels={"time": "Dzień", "prcp": "mm"},
        )
        return (
            [dcc.Graph(figure=tavg_fig)],
            [dcc.Graph(figure=wspd_fig)],
            [dcc.Graph(figure=pres_fig)],
            [dcc.Graph(figure=prcp_fig)],
        )

    tavg_fig = px.line(
        df_preprocessed,
        x="time",
        y="tavg",
        title=f"Średnia temperatura dla {city} w ostatnich {days} dniach",
        height=TAVG_HEIGHT,
        labels={"time": "Dzień", "tavg": "°C"},
    )
    wspd_fig = px.line(
        df_preprocessed,
        x="time",
        y="wspd",
        title=f"Średnia prędkość wiatru w {city} w ostatnich {days} dniach",
        height=WSPD_HEIGHT,
        labels={"time": "Dzień", "wspd": "km/h"},
    )
    pres_fig = px.line(
        df_preprocessed,
        x="time",
        y="pres",
        title=f"Średnie ciśnienie atmosferyczne w {city} w ostatnich {days} dniach",
        height=PRES_HEIGHT,
        labels={"time": "Dzień", "pres": "hPa"},
    )
    prcp_fig = px.bar(
        df_preprocessed,
        x="time",
        y="prcp",
        title=f"Opady atmosferyczne w {city} w ostatnich {days} dniach",
        height=PRCP_HEIGHT,
        labels={"time": "Dzień", "prcp": "mm"},
    )
    return (
        [dcc.Graph(figure=tavg_fig)],
        [dcc.Graph(figure=wspd_fig)],
        [dcc.Graph(figure=pres_fig)],
        [dcc.Graph(figure=prcp_fig)],
    )


@app.callback(
    Output("signal", "data"),
    [Input("city-selection", "value"), Input("days-range", "value")],
)
def compute_value(selected_city_value, days_range_value):
    """
    Stores the selected city and days value in dcc.Store.

    :param selected_city_value: City selected from the dropdown
    :param days_range_value: Number of days selected from the slider
    :return: Dictionary with the selected city and days range
    """
    return {"City": selected_city_value, "Days": days_range_value}


def filter_city_days(df_input, city, days):
    """
    Filters the DataFrame for the selected city and days range.

    :param df_input: Input DataFrame
    :param city: Selected city or None for all cities
    :param days: Number of days to look back
    :return: Filtered DataFrame
    """
    max_date = df_input["time"].max()
    min_date = max_date - pd.Timedelta(days=days)
    filtered_df = df_input[df_input["time"] >= min_date]

    if city:
        filtered_df = filtered_df[filtered_df["City"] == city]

    return filtered_df


if __name__ == "__main__":
    app.run_server(debug=True)
