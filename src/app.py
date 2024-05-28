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
    # try 'FileSystemCache' if you don't want to setup redis
    "CACHE_TYPE": "redis",
    "CACHE_REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)



# źródło danych

df = get_data(52.409538, 16.931992, 30)
print(df)
fig = px.line(df, x="time", y="tavg")

# App layout

app.layout = [
    html.Div(className='row', children='My First App with Data, Graph, and Controls',
             style={'textAlign': 'center', 'color': 'blue', 'fontSize': 30}),

        html.Div(className='six columns', children=[
            dcc.Graph(figure=fig, id='histo-chart-final')
        ])
]

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
