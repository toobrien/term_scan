from dash import Dash
from dash_core_components import Graph
from dash_html_components import Div, Table, Tr, Td
from dash_html_components.Figure import Figure
from data.contracts.contract_store import contract_store
from data.spread_set import spread_set_row, spread_set_index
from datetime import datetime
from json import loads
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlite3 import connect
from numpy import arange, array

def create_row(spread_set):
    rows = spread_set.get_rows()
    spreads = {}

    i_id = spread_set_index["id"]
    i_dl = spread_set_index["days_listed"]
    i_stl = spread_set_index["settle"]
    i_mt = spread_set_index["m_tick"]

    fig = make_subplots(
        rows = 2,
        cols = 1,
        row_heights = [ 0.8, 0.2 ],
        subplot_titles = [ 
            str(spread_set.get_id()),
            #"m_tick"
        ],
        shared_xaxes = "rows",
        vertical_spacing = 0.1
    )

    fig.update_layout(
        #xaxis_title = "days_listed",
        #yaxis_title = "settle",
        width = 1200,
        height = 600
    )

    # settlements
    for row in rows:
        id = row[i_id]
        if id not in spreads:
            spreads[id] = [] 
        spreads[id].append(row)

    for id, spread in spreads.items():
        fig.add_trace(
            go.Scatter(
                x = [ row[i_dl] for row in spread ],
                y = [ row[i_stl] for row in spread ],
                name = str(id),
                mode = "markers",
            ),
            row = 1,
            col = 1
        )

    # median settlement    
    median = spread_set.get_median()
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

    # m_tick: sort and remove duplicates
    mt = {
        int(row[i_dl]): row[i_mt]
        for row in rows if row[i_mt] is not None
    }
    mt = [ (dl, mt) for dl, mt in mt.items() ]
    mt.sort(key = lambda x: x[0])

    mx = [ d[0] for d in mt ]
    my = [ d[1] for d in mt ]

    fig.add_trace(
        go.Scatter(
            x = mx,
            y = my,
            name = "m_tick",
            mode = "markers",
            marker = { "color": "#FF0000" }
        ),
        row = 2,
        col = 1
    )

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
