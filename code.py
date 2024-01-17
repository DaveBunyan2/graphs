def create_graph(data, id, title):
    fig = update_figure(data, title)
    
    graph = dcc.Graph(id=id, figure=fig)

    return graph

def update_figure(data, title):
    timestamps, values = zip(*data)
    
    # Create a Scatter trace with the data
    trace = go.Scatter(x=timestamps, y=values, mode='lines', line=dict(color='blue'))
    
    # Create a Figure with the trace
    fig = go.Figure(data=[trace])
    update_layout(fig, title)
    return fig

def update_layout(fig, title):
    # Update layout properties
    fig.update_layout(
        paper_bgcolor='#000000',  # Background color of the entire plot
        plot_bgcolor='#2d2d2d',   # Background color of the plot area
        xaxis=dict(
            title='Timestamp',
            tickfont=dict(color='#e7e7e7'),  # Color of tick labels on the X-axis
            title_font=dict(color='#e7e7e7'),  # Color of the X-axis title
            showgrid=False,
        ),  
        yaxis=dict(
            title='Values',
            tickfont=dict(color='#e7e7e7'),  # Color of tick labels on the Y-axis
            title_font=dict(color='#e7e7e7'),  # Color of the Y-axis title
        ),     
        title=sensor_types[title],         # Plot title
        title_font=dict(size=24, color='#e7e7e7'),  # Title font size and color
        font=dict(color='#e7e7e7'),   # Font color for axis labels
        xaxis_linecolor='#878787',
        yaxis_gridcolor='#878787',
        yaxis_linecolor='#878787',
    )
