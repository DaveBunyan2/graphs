import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import time


from graph_functions import create_graph, create_3d_model
from utils import get_initial_dates, get_sensor_dictionaries
from db_connection import create_connection_pool
from extract_data import extract_data, extract_last, extract_last_x_data
from layout_functions import generate_sensor_row

 
app = dash.Dash(suppress_callback_exceptions=True)

initial_start_date, initial_error_date, initial_end_date = get_initial_dates()
connection_pool = create_connection_pool()
temperature_sensor_data, amp_sensor_data, water_sensor_data, door_sensor_data = get_sensor_dictionaries(connection_pool)

line_color, mrk_clr = '#2d2d2d', '#2d2d2d'
marker_colors = [mrk_clr] * 12
marker_sizes = [10] * 12

fig = create_3d_model(temperature_sensor_data, amp_sensor_data)


app.layout = html.Div(children=[
    html.H1(children='Freezer Dashboard', className='header'),
    dcc.Interval(
        id='main-interval',
        interval=5 * 1000,
        n_intervals=0
    ),
    dcc.Store(id='state-store', data={'sensor_id': None}),
    
    html.Div([
        html.Div([
            html.Div([
                dcc.Graph(
                    id='scatter-plot',
                    figure=fig,
                    style={'height': '750px', 'width': '500px', 'margin': '10px', 'borderRadius': '10px'}
                )
            ], style={'flex': 3}),
            html.Div([
                html.Div([
                    generate_sensor_row(
                        'Temperature', temperature_sensor_data, 1, 4, connection_pool),
                    generate_sensor_row(
                        'Temperature', temperature_sensor_data, 5, 8, connection_pool),
                    generate_sensor_row('Amp', amp_sensor_data, 1, 4, connection_pool),
                    # generate_sensor_row('Water level', water_sensor_data, 1, 2, connection_pool),
                    # generate_sensor_row('Door', door_sensor_data, 1, 1, connection_pool)
                ], id='main-content',
                    className='main-div'),
                html.Div(
                    id='graph-content',
                    style={'display': 'none'}
                ),
                
            ],
                style={'flex': 6}
            ),
            html.Div(
                    children=[
                        'Compressor off'
                    ],
                    id='compressor-status',
                    style={'flex': 0.5}
                )
        ],
            style={'display': 'flex', 'flexDirection': 'row'}
        )
    ], style={'display': 'flex', 'flexDirection': 'column'})
])

types = [{**temperature_sensor_data, **amp_sensor_data}[item]['type'] 
        for item in {**temperature_sensor_data, **amp_sensor_data}]
ids = [{**temperature_sensor_data, **amp_sensor_data}[item]['id'] 
      for item in {**temperature_sensor_data, **amp_sensor_data}]
max_vals = [{**temperature_sensor_data, **amp_sensor_data}[item]['max_value'] 
      for item in {**temperature_sensor_data, **amp_sensor_data}]
min_vals = [{**temperature_sensor_data, **amp_sensor_data}[item]['min_value'] 
      for item in {**temperature_sensor_data, **amp_sensor_data}]

@app.callback(
    Output('scatter-plot', 'clickData'),
    Output('graph-content', 'children'),
    Output('graph-content', 'style'),
    Output('state-store', 'data'),
    Output('scatter-plot', 'figure'),
    Output('compressor-status', 'children'),
    *[
        Output(f'{sensor_type}-{sensor_id}-main', 'children') 
        for sensor_type, sensor_id in zip(types, ids)
    ],
    *[
        Output(f'{sensor_type}-{sensor_id}-div', 'className')
        for sensor_type, sensor_id in zip(types, ids)
    ],
    Input('main-interval', 'n_intervals'),
    Input('scatter-plot', 'clickData'),
    *[
        Input(f'{sensor_type}-{sensor_id}-div', 'n_clicks')
        for sensor_type, sensor_id in zip(types, ids)
    ],
    State('state-store', 'data'),
    prevent_initial_call=True
)
def update_main_page(interval, click_data, *clicked_div):
    # Get ID of what triggered callback
    ctx = dash.callback_context
    fig_data = fig.data

    initial_start_date, initial_error_date, initial_end_date = get_initial_dates()

    marker_colors = [mrk_clr] * 12
    marker_sizes = [10] * 12
    # Get last sensor values from database
    sensor_data = {}
    for sensor in {**temperature_sensor_data, **amp_sensor_data}.values():
        sensor_data[f"{sensor['type']}-{sensor['id']}"] = extract_last(sensor['id'], sensor['type'], connection_pool)[0]


    if sensor_data['amp-1'][0] > 1:
        compressor_status = 'Compressor on'
    else:
        compressor_status = 'Compressor off'
    # Color sensor divs red if value out of range
    display_list = ['sensor-details'] * (len(temperature_sensor_data.keys()) + len(amp_sensor_data.keys()))
    # for i, key in enumerate(sensor_data):
    #         if sensor_data[key][0] < min_vals[i] or sensor_data[key][0] > max_vals[i] or (sensor_data[key][0] < 0 and i > 7) or sensor_data[key][0] < -998:
    #             display_list[i] = 'out-of-range'
    #             marker_colors[i] = '#850014'
    #             fig_data[-1].marker.color = marker_colors
        
    # Check if interval triggered the callback
    if ctx.triggered_id == 'main-interval':
        # Check if a graph is being displayed on the main page
        if clicked_div[-1]['sensor_id'] == None:
            return None, None, {'display': 'flex'}, {'sensor_id': None}, {'data': fig_data, 'layout': fig.layout}, compressor_status, *[sensor_data[key] for key in sensor_data], *display_list
        else:
            # Get sensor details being displayed
            sensor_type, sensor_id = clicked_div[-1]['sensor_id'].split()
            sensor_id = int(sensor_id)
            sensor_name = f'{sensor_type.title()} sensor {sensor_id}'

            # Get data for sensor
            data = extract_data(initial_start_date, initial_end_date, sensor_id, sensor_type, connection_pool)
            graph = create_graph(data, 'sensor-graph-content', sensor_name)


            state = {'sensor_id': f'{sensor_type} {sensor_id}'}

            clicked_sensor = sensor_id
            if sensor_type == 'amp':
                clicked_sensor += len(temperature_sensor_data.keys())

            marker_colors[clicked_sensor - 1] = 'blue'
            marker_sizes[clicked_sensor - 1] = 25

            fig_data[-1].marker.color = marker_colors
            fig_data[-1].marker.size = marker_sizes

            display_list[clicked_sensor - 1] = 'selected-div'
            return None, graph, {'display': 'flex'}, state, {'data': fig_data, 'layout': fig.layout}, compressor_status, *[sensor_data[key] for key in sensor_data], *display_list
    
    if click_data is not None:
        clicked_coordinates = [
            click_data['points'][0]['x'],
            click_data['points'][0]['y'],
            click_data['points'][0]['z']
        ]
        for sensor_name, sensor_info in {**temperature_sensor_data, **amp_sensor_data}.items():
            if clicked_coordinates == sensor_info['coords']:
                sensor_type = sensor_info['type']
                sensor_id = sensor_info['id']
                data = extract_data(initial_start_date, initial_end_date, sensor_id, sensor_type, connection_pool)
                graph = create_graph(data, 'sensor-graph-content', sensor_name)
                state = {'sensor_id': f'{sensor_type} {sensor_id}'}
                clicked_sensor = sensor_id
                if sensor_type == 'amp':
                    clicked_sensor += len(temperature_sensor_data.keys())

        marker_colors[clicked_sensor - 1] = 'blue'
        marker_sizes[clicked_sensor - 1] = 25
        
        fig_data[-1].marker.color = marker_colors       
        fig_data[-1].marker.size = marker_sizes

        display_list[clicked_sensor - 1] = 'selected-div'
        return None, graph, {'display': 'flex'}, state, {'data': fig_data, 'layout': fig.layout}, compressor_status, *[sensor_data[key] for key in sensor_data], *display_list
    
    sensor_type = ctx.triggered_id.split('-')[0]
    sensor_id = int(ctx.triggered_id.split('-')[1])
    sensor_name = f'{sensor_type.title()} sensor {sensor_id}'

    data = extract_data(initial_start_date, initial_end_date, sensor_id, sensor_type, connection_pool)
    graph = create_graph(data, 'sensor-graph-content', sensor_name)

    clicked_sensor = sensor_id
    if sensor_type == 'amp':
        clicked_sensor += len(temperature_sensor_data.keys())    
        
    marker_colors[int(clicked_sensor) - 1] = 'blue'
    marker_sizes[clicked_sensor - 1] = 25

    fig_data[-1].marker.color = marker_colors
    fig_data[-1].marker.size = marker_sizes

    display_list[clicked_sensor - 1] = 'selected-div'
    state = {'sensor_id': f'{sensor_type} {sensor_id}'}
    return None, graph, {'display': 'flex'}, state, {'data': fig_data, 'layout': fig.layout}, compressor_status, *[sensor_data[key] for key in sensor_data], *display_list


if __name__ == '__main__':
    app.run_server(debug=True)
