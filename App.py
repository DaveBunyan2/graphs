import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import random
import datetime
from collections import deque

app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div(
    [
        dcc.Graph(id="real-time-graph"),
        dcc.Interval(
            id="interval-component",
            interval=1 * 1000,  # in milliseconds
            n_intervals=0,
        ),
    ]
)

# Initialize data for the graph
X = deque(maxlen=20)
Y = deque(maxlen=20)

# Dummy data for initialization
for i in range(20):
    X.append(datetime.datetime.now() - datetime.timedelta(seconds=20 - i))
    Y.append(random.randint(0, 100))

# Callback to update the graph data
@app.callback(
    Output("real-time-graph", "figure"),
    [Input("interval-component", "n_intervals")],
)
def update_graph(n):
    global X, Y
    X.append(datetime.datetime.now())
    Y.append(random.randint(0, 100))

    fig = px.line(
        pd.DataFrame({"X": list(X), "Y": list(Y)}), x="X", y="Y", title="Real-time Graph"
    )

    return fig

if __name__ == "__main__":
    app.run_server(debug=True)
