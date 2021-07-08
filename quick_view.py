from dash import Dash
from dash_core_components import Graph
from dash_html_components import Div, Table, Tr, Td
from dash_html_components.Figure import Figure
from data.contracts.contract_store import contract_store
from data.spread_set import spread_set_row, spread_set_index
from datetime import datetime, date, timedelta
from json import loads
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlite3 import connect
from numpy import array
from numpy.random import randn

def create_row(spread_set):
    rows = spread_set.get_rows()
    spreads = {}

    i_id = spread_set_index["id"]
    i_dt = spread_set_index["date"]
    i_dl = spread_set_index["days_listed"]
    i_stl = spread_set_index["settle"]
    i_mt = spread_set_index["m_tick"]

    # figure
    fig = make_subplots(
        rows = 2,
        cols = 1,
        row_heights = [ 0.8, 0.2 ],
        subplot_titles = [ 
            str(spread_set.get_id()),
        ],
        shared_xaxes = True,
        vertical_spacing = 0.02
    )

    fig.update_layout(
        #xaxis_title = "days_listed",
        #yaxis_title = "settle",
        width = 1200,
        height = 600
    )

    # settlement traces
    for row in rows:
        id = row[i_id]
        if id not in spreads:
            spreads[id] = [] 
        spreads[id].append(row)

    window = date.today() - timedelta(days= 5)
    next_opc = 0.1
    opc_step = 0.6 / len(spreads)

    for id, spread in spreads.items():
        latest = date.fromisoformat(spread[-1][i_dt])
        active = window <= latest
        _color = None if active else "#0000FF"
        _opacity = 1 if active else next_opc
        next_opc += opc_step

        fig.add_trace(
            go.Scatter(
                x = [ row[i_dl] for row in spread ],
                y = [ row[i_stl] for row in spread ],
                name = str(id),
                mode = "markers",
                opacity = _opacity,
                marker = { "color": _color }
            ),
            row = 1,
            col = 1
        )

    # median trace    
    median = spread_set.get_stat["settle"]["median"]
    max_dl = array([row[i_dl] for row in rows]).max(0)
    fig.add_trace(
        go.Scatter(
            x = [ 0, max_dl ],
            y = [ median, median ],
            name = "median",
            mode = "lines",
            marker = { "color": "#FF0000" }
        )
    )

    # m_tick
    mt = spread_set.get_stat["m_tick"]["rows"]

    # m_tick main
    fig.add_trace(
        go.Scatter(
            x = [ row[0] for row in mt ],
            y = [ row[1] for row in mt ],
            name = "m_tick",
            mode = "markers",
            marker = { "color": "#0000FF" }
        ),
        row = 2,
        col = 1
    )
    
    # m_tick 0
    fig.add_trace(
        go.Scatter(
            x = [ 0, max_dl ],
            y = [ 0, 0 ],
            name = "0",
            marker = { "color": "#FF0000" }
        ),
        row = 2,
        col = 1
    )

    # construct row
    settle_graph = Graph(
        id = str(spread_set.get_id()),
        figure = fig
    )
    settle_cell = Td([settle_graph])
    row = Tr([settle_cell])
    
    return row


if __name__=="__main__":
    with open('./config.json') as fd:
        app = Dash(__name__)
        rows = []

        config = loads(fd.read())
        cur = connect(config["db_path"])

        data = contract_store(
            "SM", 
            ["2010-01-01", "2025-01-01"], 
            cur
        )
        
        matches = [
            ((9, 0, 'A'), (11, 1, 'B')),    #('+V10', '-Z11')
            ((0, 1, 'A'), (11, 1, 'B')),    #('+F11', '-Z11'))
            ((2, 1, 'A'), (11, 1, 'B')),    #('+H11', '-Z11'))
            ((4, 1, 'A'), (11, 1, 'B'))     #('+K11', '-Z11'))
        ]

        stats = [
            "settle", 
            "m_tick",
            #"vol",
            #"beta",
            #"r_2"
        ]

        start = datetime.now()
        spread_sets = [ data.get_spread_set(m) for m in matches ]
        
        for spread_set in spread_sets:
            spread_set.add_stats(stats)

        for spread_set in spread_sets:
            rows.append(create_row(spread_set))

        table = Table(rows)
        app.layout = Div(children = [ table ])

        elapsed = datetime.now() - start
        print(len(spread_sets), elapsed)

        app.run_server(debug = True)
