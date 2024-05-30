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
df = get_data(date_range)

# App layout
app.layout = html.Div([
    html.H1(children="Prognoza pogody"),
    html.Div(
        children="""
            Aplikacja napisana w Dashu
        """
    ),
    html.Div([
        html.H3(children="Miasto", className="card"),
        dcc.Dropdown(
            df["City"].unique(),
            value="Poznań",
            id="city-selection",
            multi=False,
        ),
    ]),
    html.Div([
        html.H3(children="Zakres dni", className="card"),
        dcc.Slider(
            id='days-range',
            min=1,
            max=30,
            step=1,
            value=30,
            marks={i: str(i) for i in range(1, date_range + 1)},
        ),
    ]),
    html.Div(className='graph', children=[
        dcc.Loading(
            id="loading-1",
            type="default",
            children=dcc.Graph(id='chart')
        )
    ]),
    dcc.Store(id="signal"),
])

@cache.memoize()
def global_store(city, days):
    """
    Fetches and processes the data for the selected city and days range.

    :param city: Selected city
    :param days: Number of days to look back
    :return: Filtered DataFrame for the selected city and days range
    """
    tmp = filter_city_days(df, city, days)
    time.sleep(3)  # Simulating a long computation
    return tmp

@app.callback(
    Output("chart", "figure"),
    Input("signal", "data"),
)
def update_graph(value):
    """
    Updates the plot according to the selected city and days range.

    :param value: Selected city and days value from dcc.Store
    :return: Updated plotly figure
    """
    df_preprocessed = global_store(value["City"], value["Days"])

    fig = px.line(
        df_preprocessed,
        x="time",
        y="tavg",
    )

    fig.update_layout(title=f'Average Temperature in {value["City"]} for the last {value["Days"]} days')

    return fig

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
    :param city: Selected city
    :param days: Number of days to look back
    :return: Filtered DataFrame
    """
    filtered_df = df_input[df_input["City"] == city]
    max_date = filtered_df["time"].max()
    min_date = max_date - pd.Timedelta(days=days)
    tmp = filtered_df[filtered_df["time"] >= min_date]
    return tmp

if __name__ == '__main__':
    app.run_server(debug=True)

'''
app.layout = html.Div(
    children=[
        html.H1(children="Zgony na Covid a przyjęte dawki szczepień"),
        html.Div(
            children="""
        Aplikacja napisana w Dashu
    """
        ),
        html.Div(
            [
                html.H3(children="Płeć", className="card"),
                dcc.Dropdown(
                    df["plec"].unique(),
                    df["plec"].unique(),
                    id="gender-selection",
                    multi=True,
                ),
            ]
        ),
        
        html.Br(),
        html.Div(
            [
                html.H3(children="Wiek", className="card"),
                dcc.RangeSlider(
                    min=1,
                    max=max(df.wiek),
                    value=[30, 80],
                    id="age-selection",
                ),
            ]
        ),
        html.Div([dcc.Checklist(id="select_columns")]),
        html.Div(dcc.Graph(id="chart")),
        html.Div(dash_table.DataTable(id="tbl")),
        # signal value to trigger callbacks
        dcc.Store(id="signal"),
    ]
)



def filter_age_gender(df_input, age, gender):
    """

    :param df_input:
    :param age:
    :param gender:
    :return:
    """
    if age is None:
        age = (min(df_input.wiek), max(df_input.wiek))
    if gender is None:
        gender = df_input.plec.unique()
    tmp = df_input.loc[df_input.loc[:, "plec"].isin(gender), :]  # pylint: disable=E1101
    tmp = tmp[tmp.loc[:, "wiek"] <= age[1]]
    tmp = tmp[tmp.loc[:, "wiek"] >= age[0]]
    return tmp


# perform expensive computations in this "global store"
# these computations are cached in a globally available
# redis memory store which is available across processes
# and for all time.
@cache.memoize()
def global_store(value):
    """

    :param value:
    :return:
    """
    gender = value["gender"]
    age = value["age"]

    tmp = filter_age_gender(df, age, gender)
    tmp = (
        tmp.groupby("dawka_ost")
        .agg({"liczba_zaraportowanych_zgonow": sum})
        .reset_index()
    )
    # "dlugie obliczenia"
    time.sleep(3)
    return tmp


@app.callback(
    Output("signal", "data"),
    [Input("gender-selection", "value"), Input("age-selection", "value")],
)
def compute_value(selected_gender_value, age_selection_value):
    """

    :param selected_gender_value:
    :param age_selection_value:
    :return:
    """
    global_store(
        {"gender": sorted(selected_gender_value), "age": sorted(age_selection_value)}
    )

    return {"gender": selected_gender_value, "age": age_selection_value}


@app.callback(
    Output("chart", "figure"),
    Input("signal", "data"),
)
def update_graph(value):
    """
    Updates the plot according to the selected values

    :param selected_gender_value:
    :param age_selection_value:
    :return: updated plotly figure
    """
    df_preprocessed = global_store(value)

    fig = px.bar(
        df_preprocessed,
        x="dawka_ost",
        y="liczba_zaraportowanych_zgonow",
        color="dawka_ost",
        title="Zgony według zaszczepienia",
        labels={
            "dawka_ost": "Zaszczepienie",
            "liczba_zaraportowanych_zgonow": "Liczba zgonów",
        },
    )

    fig.update_layout(barmode="overlay")

    return fig


@app.callback(
    [Output("select_columns", "value"), Output("select_columns", "options")],
    Input("signal", "data"),
)
def update_available_columns(value):
    """

    :param value:
    :return:
    """
    df_preprocessed = global_store(value)

    return df_preprocessed.columns, df_preprocessed.columns


@app.callback(
    Output("tbl", "data"), [Input("signal", "data"), Input("select_columns", "value")]
)
def update_table(value, selected_columns):
    """

    :param value:
    :param selected_columns:
    :return:
    """
    df_preprocessed = global_store(value)
    return df_preprocessed[selected_columns].to_dict("rows")

'''

if __name__ == "__main__":
    app.run_server(debug=True)
