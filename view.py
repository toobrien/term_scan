from dash import Dash
from dash.dependencies import Input, Output, State
from dash_core_components import Graph, Dropdown
from dash_html_components import \
Div, Table, Tr, Td, P, Button, Textarea
from data.contracts.contract_store import contract_store
from data.spread_set import spread_set_index
from data.terms.terms_store import terms_store
from datetime import datetime, date, timedelta
from json import loads, dumps
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlite3 import connect
from numpy import array


# GLOBAL VARIABLES


config = None
db = None

with open('./config.json') as fd:
    config = loads(fd.read())
    db = connect(config["db_path"])

app = Dash(__name__)

current_scan = None
scan_defs = {}
match_data = {}
figures = {}


# FUNCTIONS


# add a subplot for a given statistic
#   fig:            settlemnt graph object
#   spread_set:     data for fig
#   plot_def:       [ str: stat_name, str: color, int: row ]
#   x_lim:          max of days-listed domain
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


# plot settlement values every spread in a related set,
# along with subplots for statistics of interest
def create_graph(spread_set, stats):
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
        width = 800,
        height = 600
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

    # construct graph
    graph = Graph(
        id = spread_set.get_id(),
        figure = fig
    )           
    
    return graph


# sequence:
#   in:
#       0,119,A      
#       +1,119,B 
#   out:
#       [
#           [ "0", "119", "A" ],
#           [ "+1", "119", "B" ]
#       ]
# calendar:
#   in:
#       Q,Z,0,1,A
#       +1,Z,+0,1,B
#   out:
#       [
#           [ "Q", "Z", "0", "3", "A" ],
#           [ "+1", "Z", "+0", "1", "A" ]
#       ]
def parse_legs(legs):
    pass


# in:
#   settle:abs=-10,10
#   m_tick:abs=0.2,1
#   vol:std=-2,-1;1,2
#   beta:abs=0,0.1
#   r_2:abs=0,0.3
# out:
#   [
#       { 
#           type: "vol",
#           mode: "stdev",
#           range: [ [ -2, -1 ], [ 1, 2 ] ] 
#       },
#           ...
#   ]
def parse_filters(filters):
    pass


# update scan parameters as the user edits them
@app.callback(
    Input("name", "value"),
    Input("contract", "value"),
    Input("type", "value"),
    Input("date_range", "value"),
    Input("result_limit", "value"),
    Input("legs", "value"),
    Input("filters", "value")
)
def update_current_scan(
    name, contract, type, 
    date_range, legs, filters
):
    pass


# update execute current_scan
@app.callback(
    Input("start", "n_clicks"),
    Output("results", "value")
)
def start_scan():
    pass


# delete selected scan
@app.callback(
    Input("save", "nclicks"),
    State("save_delete", "value")
)
def save_scan(save, save_delete):
    scan_defs[save_delete] = current_scan
    config["scans"] = [ dumps(scan) for scan in scan_defs ]
    
    with open('./config.json', "w") as fd:
        fd.write(dumps(config))



# save current scan under name in save_delete field
@app.callback(
    Input("delete", "nclicks"),
    State("save_delete", "value"),
    Output("scan", "children")
)
def delete_scan(delete, save_delete):
    scan_options = []
    scans = []

    for name, dfn in scan_defs:
        if name != save_delete:
            scans.append(dumps(dfn))
            scan_options.append(
                {
                    "label": name,
                    "value": name
                }
            )
    
    config["scans"] = scans
    
    with open('./config.json', "w") as fd:
        fd.write(dumps(config))

    return scan_options


# generate and store graph objects for
# selected spread data
@app.callback(
    Input("to_view", "value"),
    Output("viewing", "children")
)
def generate_figures(to_view):
    figures.clear()
    viewing_options = []

    # stats computed in this scan
    # TODO: decouple (just compute all?)
    stats = [
        f["type"] 
        for f in current_scan["filters"]
    ]

    # generate, store figures and set viewing options
    for match in to_view.split("\n"):
        if match in match_data:
            spread_set = match_data[match]
            figures[match] = create_graph(spread_set, stats)
            viewing_options.append(
                {
                    "label": match,
                    "value": match
                }
            )

    return viewing_options


# view selected figure
@app.callback(
    Input("viewing", "value"),
    Output("plots", "children")
)
def update_graph(viewing):
    return figures[viewing]


def get_layout(scans):
    return Table([
        Tr([
            # controls
            Td([ 
                Table([
                    Tr([
                        Td("scan"),
                        Td(Dropdown(id = "scan", options = scans))
                    ]),
                    Tr([
                        Td([
                            Button(id = "save", children = "save"),
                            Button(id = "delete", children = "delete")
                        ]),
                        Td(Input(id = "save_delete", type = "text"))
                    ]),
                    Tr([
                        Td("name"),
                        Td(Input(id = "name", type = "text"))
                    ]),
                    Tr([
                        Td("contract"),
                        Td(Input(id = "contract", type = "text"))
                    ]),
                    Tr([
                        Td("type"),
                        Td(Input(id = "type", type = "text"))
                    ]),
                    Tr([
                        Td("date_range"),
                        Td(Input(id = "date_range", type = "text"))
                    ]),
                    Tr([
                        Td("result_limit"),
                        Td(Input(id = "result_limit", type = "text"))
                    ]),
                    Tr([
                        Td("legs"),
                        Td(Textarea(id = "legs", rows = 15))
                    ]),
                    Tr([
                        Td("filters"),
                        Td([
                            Textarea(id = "filters", rows = 15)
                        ])
                    ]),
                    Tr([
                        Td("results"),
                        Td(Textarea(id = "scan_results", rows = 30))
                    ]),
                    Tr([
                        Td(Button(id = "start", children = "start")),
                        Td([])
                    ]),
                    Tr([
                        Td("to_view"),
                        Td([
                            Textarea(id = "to_view", rows = 15)
                        ])
                    ]),
                    Tr([
                        Td("viewing"),
                        Td(Dropdown(id = "viewing"))
                    ])
                ], id = "controls")
            ], width = 400),
            # plots
            Td(Div(id = "plots"),width = 800)
        ])
    ])

if __name__=="__main__":
        # scan
        '''
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

        # create graphs
        graphs = []
        for spread_set in spread_sets:
            graphs.append(create_graph(spread_set, stats))
        '''

        # populate layout with saved scans
        scans = [
            { "label": k, "value": k } 
            for k, v in config["scans"]
        ]
        app.layout = get_layout(scans)

        # set scan_defs
        for k, v in scans:
            scan_defs[k] = v

        #elapsed = datetime.now() - start
        #print(len(spread_sets), elapsed)

        app.run_server(debug = True)