from dash.dependencies import Output, Input
from dash import html, dcc, Dash
import plotly
import plotly.graph_objs as go
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn
from obtener_datos import obtener_datos_activo_id_activo_petroleo


app_dash = Dash(__name__, requests_pathname_prefix="/dash/")

app_dash.layout = html.Div(
    [
        html.H1(children="Graficos de PETROLI", style={"textAlign": "center"}),
        dcc.Graph(id="live-graph", animate=True),
        dcc.Interval(id="graph-update", interval=3 * 1000),
    ]
)


@app_dash.callback(
    Output("live-graph", "figure"), [Input("graph-update", "n_intervals")]
)
def update_graph_scatter(input_data):
    df = pd.DataFrame(obtener_datos_activo_id_activo_petroleo(1))
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')

    data = plotly.graph_objs.Scatter(
        x=list(df["timestamp"]),
        y=df["presion"],
        name="Scatter",
        mode="lines+markers+text",
        textfont=dict(color="#E58606"),
        marker=dict(color="#5D69B1", size=8),
        line=dict(color="#52BCA3", width=1),
    )

    five_seconds_ago = pd.Timedelta(seconds=120)
    

    print(max(df["timestamp"]) - five_seconds_ago)

    return {
        "data": [data],
        "layout": go.Layout(
            xaxis=dict(
                range=[max(df["timestamp"]) - five_seconds_ago, df["timestamp"].max()]
            ),
            yaxis=dict(range=[min(df["presion"]), max(df["presion"])]),
        ),
    }


app = FastAPI()

app.mount("/dash", WSGIMiddleware(app_dash.server))

if __name__ == "__main__":
    uvicorn.run(app="main:app", reload=True, port=8080)
