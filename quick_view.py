from dash import Dash
from dash_core_components import Graph
from dash_html_components import Div, Table, Tr, Td
from data.contracts.contract_store import contract_store
from data.spread_set import spread_set_index
from data.terms.terms_store import terms_store
from datetime import datetime, date, timedelta
from json import loads
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlite3 import connect
from numpy import array

def stat_subplot(fig, spread_set, plot_def, x_lim):
    stat = plot_def[0]
    color = plot_def[1]
    row_num = plot_def[2]

    rows = spread_set.get_stat(stat)["rows"]

    # stat trace
    fig.add_trace(
        go.Scatter(
            x = [ row[0] for row in rows ],
            y = [ row[1] for row in rows ],
            name = plot_def[0],
            mode = "markers",
            marker = { "color": color }
        ),
        row = row_num,
        col = 1
    )
    
    # 0 trace
    fig.add_trace(
        go.Scatter(
            x = [ 0, x_lim ],
            y = [ 0, 0 ],
            name = f"{plot_def[0]} 0",
            marker = { "color": "#FF0000" }
        ),
        row = row_num,
        col = 1
    )


def create_row(spread_set, stats):
    rows = spread_set.get_rows()
    spreads = {}

    i_pid = spread_set_index["plot_id"]
    i_dt = spread_set_index["date"]
    i_dl = spread_set_index["days_listed"]
    i_stl = spread_set_index["settle"]

    # figure
    row_count = 1 + len(stats)
    scatter_row_height = 1 - 0.1 * (row_count - 1)
    rhs = [ 0.1 for i in range(row_count) ]
    rhs[0] = scatter_row_height

    fig = make_subplots(
        rows = row_count,
        cols = 1,
        row_heights = rhs,
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
        height = 800
    )

    # settlement traces
    for row in rows:
        plot_id = row[i_pid]
        if plot_id not in spreads:
            spreads[plot_id] = [] 
        spreads[plot_id].append(row)

    window = date.today() - timedelta(days= 5)
    next_opc = 0.1
    opc_step = 0.6 / len(spreads)

    for plot_id, spread in spreads.items():
        latest = date.fromisoformat(spread[-1][i_dt])
        active = window <= latest
        _color = None if active else "#0000FF"
        _opacity = 1 if active else next_opc
        next_opc += opc_step

        fig.add_trace(
            go.Scatter(
                x = [ row[i_dl] for row in spread ],
                y = [ row[i_stl] for row in spread ],
                name = str(plot_id),
                mode = "markers",
                opacity = _opacity,
                marker = { "color": _color }
            ),
            row = 1,
            col = 1
        )

    # median trace    
    median = spread_set.get_stat("settle")["median"]
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

    # add stat subplots
    colors = [ "#0000FF", "#FF00FF", "#00FF00", "#FF0000" ]
    plot_defs = [
        [ stats[i], colors[i], i + 2 ] 
        for i in range(len(stats)) 
    ]
    for plot_def in plot_defs:
        stat_subplot(fig, spread_set, plot_def, max_dl)

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

        mode = "terms"

        if mode == "contract":
            data = contract_store(
                "SM", 
                [ "2010-01-01", "2025-01-01" ],
                cur
            )
            matches = [
                ((9, 0, 'A'), (11, 1, 'B')),    #('+V10', '-Z11')
                ((0, 1, 'A'), (11, 1, 'B')),    #('+F11', '-Z11'))
                ((2, 1, 'A'), (11, 1, 'B')),    #('+H11', '-Z11'))
                ((4, 1, 'A'), (11, 1, 'B'))     #('+K11', '-Z11'))
            ]
        elif mode == "terms":
            data = terms_store(
                "ED",
                [ "2000-01-01", "2035-01-01" ],
                cur
            )
            matches = [
                ((15, 'A'), (32, 'B')),
                ((19, 'A'), (24, 'B'))
            ]

        stats = [
            "settle", 
            "m_tick",
            "vol",
            "beta",
            "r_2"
        ]

        start = datetime.now()
        spread_sets = [ data.get_spread_set(m) for m in matches ]
        
        for spread_set in spread_sets:
            spread_set.add_stats(stats)

        for spread_set in spread_sets:
            rows.append(create_row(spread_set, stats))

        table = Table(rows)
        app.layout = Div(children = [ table ])

        elapsed = datetime.now() - start
        print(len(spread_sets), elapsed)

        app.run_server(debug = True)