import os
import time
import pandas as pd  # type: ignore
from dash import Dash, html, dcc, dash_table  # type: ignore
from dash.dependencies import Input, Output  # type: ignore
from flask_caching import Cache  # type: ignore
import plotly.express as px  # type: ignore
from helpers import *

app = Dash(__name__, assets_folder="../assets")

server = app.server

CACHE_CONFIG = {
    # Switching to 'FileSystemCache' to avoid Redis connection issues
    "CACHE_TYPE": "filesystem",
    "CACHE_DIR": "cache-directory",
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)

# Data source
df = get_data(30)

# App layout
app.layout = html.Div(
    [
        html.H1(children="Prognoza pogody"),
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
                    marks={i: str(i) for i in range(1, 31)},
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
                                    "height": f"{pres_height}px",
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
                                    "height": f"{wspd_height}px",
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
                                    "height": f"{prcp_height}px",
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
                                    "height": f"{tavg_height}px",
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
    elif city == "Cała Polska":
        return filter_city_days(df, None, days).groupby("time").agg({"tavg": "mean", "wspd": "mean", "pres": "mean", "prcp": "sum"}).reset_index()
    else:
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
        cities = df_preprocessed["City"].unique()
        tavg_graphs = []
        wspd_graphs = []
        pres_graphs = []
        prcp_graphs = []
        for city in cities:
            city_data = df_preprocessed[df_preprocessed["City"] == city]
            tavg_fig = px.line(
                city_data,
                x="time",
                y="tavg",
                title=f"Average Temperature in {city} for the last {days} days",
                height=tavg_height,
            )
            wspd_fig = px.line(
                city_data,
                x="time",
                y="wspd",
                title=f"Wind Speed in {city} for the last {days} days",
                height=wspd_height,
            )
            pres_fig = px.line(
                city_data,
                x="time",
                y="pres",
                title=f"Pressure in {city} for the last {days} days",
                height=pres_height,
            )
            prcp_fig = px.bar(
                city_data,
                x="time",
                y="prcp",
                title=f"Precipitation in {city} for the last {days} days",
                height=prcp_height,
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
    elif city == "Cała Polska":
        tavg_fig = px.line(
            df_preprocessed,
            x="time",
            y="tavg",
            title=f"Average Temperature in Cała Polska for the last {days} days",
            height=tavg_height,
        )
        wspd_fig = px.line(
            df_preprocessed,
            x="time",
            y="wspd",
            title=f"Wind Speed in Cała Polska for the last {days} days",
            height=wspd_height,
        )
        pres_fig = px.line(
            df_preprocessed,
            x="time",
            y="pres",
            title=f"Pressure in Cała Polska for the last {days} days",
            height=pres_height,
        )
        prcp_fig = px.bar(
            df_preprocessed,
            x="time",
            y="prcp",
            title=f"Precipitation in Cała Polska for the last {days} days",
            height=prcp_height,
        )
        return (
            [dcc.Graph(figure=tavg_fig)],
            [dcc.Graph(figure=wspd_fig)],
            [dcc.Graph(figure=pres_fig)],
            [dcc.Graph(figure=prcp_fig)],
        )
    else:
        tavg_fig = px.line(
            df_preprocessed,
            x="time",
            y="tavg",
            title=f"Average Temperature in {city} for the last {days} days",
            height=tavg_height,
        )
        wspd_fig = px.line(
            df_preprocessed,
            x="time",
            y="wspd",
            title=f"Wind Speed in {city} for the last {days} days",
            height=wspd_height,
        )
        pres_fig = px.line(
            df_preprocessed,
            x="time",
            y="pres",
            title=f"Pressure in {city} for the last {days} days",
            height=pres_height,
        )
        prcp_fig = px.bar(
            df_preprocessed,
            x="time",
            y="prcp",
            title=f"Precipitation in {city} for the last {days} days",
            height=prcp_height,
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
