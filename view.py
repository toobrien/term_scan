from dash import Dash
from dash.dependencies import \
    Input, Output, State
from dash_core_components import \
    Dropdown, Graph, Input as CInput, Textarea
from dash_html_components import \
    Div, Table, Tr, Td, Button
from data.spread_set import spread_set_index
from datetime import date, timedelta
from json import loads, dumps
from numpy import array
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scan import scan
from sqlite3 import connect


# GLOBAL VARIABLES

config = None
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
        id = str(spread_set.get_id()),
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
    legs = legs.split("\n")
    parsed = []

    for leg in legs:
        parts = leg.split(",")
        parsed.append([ str(part) for part in parts])
    
    return parsed


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
    filters = filters.split("\n")
    results = []

    for filter in filters:
        parsed = {}
        parts = filter.split("=")
        lhs = parts[0]
        rhs = parts[1]
        dfn = lhs.split(":")
        rngs = rhs.split(";")

        parsed["type"] = dfn[0]
        parsed["mode"] = dfn[1]
        parsed["range"] = []

        for rng in rngs:
            lims = rng.split(",")
            parsed["range"].append(
                [ 
                    float(lims[0]),
                    float(lims[1])
                ]
            )

        results.append(parsed)

    return results


# opposite of parse_legs
def serialize_legs(legs):
    return "\n".join([ ",".join(leg) for leg in legs ])


# opposite of parse_filters
def serialize_filters(filters):
    return "\n".join(
        [
            f'{f["type"]}:{f["mode"]}={";".join([ ",".join([ str(i) for i in rng ]) for rng in f["range"] ])}'
            for f in filters
        ]
    )


# set current_scan and populate form to allow for user edits
@app.callback(
    Output("name", "value"),
    Output("contract", "value"),
    Output("type", "value"),
    Output("data_range", "value"),
    Output("result_limit", "value"),
    Output("legs", "value"),
    Output("filters", "value"),
    Input("scan", "value"),
    prevent_initial_call = True
)
def set_current_scan(scan):
    global current_scan
    current_scan = scan_defs[scan]

    return [
        current_scan["name"],
        current_scan["contract"],
        current_scan["type"],
        ",".join(current_scan["data_range"]),
        current_scan["result_limit"],
        serialize_legs(current_scan["legs"]),
        serialize_filters(current_scan["filters"])
    ]


@app.callback(
    Output("null1", "children"),
    Input("name", "value"),
    Input("contract", "value"),
    Input("type", "value"),
    Input("data_range", "value"),
    Input("result_limit", "value"),
    Input("legs", "value"),
    Input("filters", "value"),
    prevent_initial_call = True
)
def update_current_scan(
    name, contract, type, data_range,
    result_limit, legs, filters
):
    # update current scan to reflect any user edits
    current_scan["name"] = name
    current_scan["contract"] = contract
    current_scan["type"] = type
    # "2000-01-01,2030-01-01" -> [ "2000-01-01", "2030-01-01" ]
    current_scan["data_range"] = data_range.split(",")
    current_scan["result_limit"] = result_limit
    current_scan["legs"] = parse_legs(legs)
    current_scan["filters"] = parse_filters(filters)
    
    return None


@app.callback(
    Output("matches", "value"),
    Input("start", "n_clicks"),
    prevent_initial_call = True
)
def execute_current_scan(start):
    # clear previous results
    global match_data
    match_data = {}

    # execute current_scan, store results
    response = scan(
        current_scan, 
        connect(config["db_path"])
    ).execute()
    
    matches = []

    for result in response["results"]:
        match = str(result["match"])
        spread_set = result["data"]
        match_data[match] = spread_set
        matches.append(match)

    # populate matches textarea for user editing
    return "\n".join(matches)


# save selected scan from stored config
@app.callback(
    Output("null0", "children"),
    Input("save", "n_clicks"),
    State("save_delete", "value"),
    prevent_initial_call = True
)
def save_scan(save, save_delete):
    scan_defs[save_delete] = current_scan
    config["scans"] = [ dumps(scan) for _, scan in scan_defs.items() ]
    
    with open('./config.json', "w") as fd:
        fd.write(dumps(config))

    return None


# delete current scan using name in save_delete field
@app.callback(
    Output("scan", "options"),
    Input("delete", "n_clicks"),
    State("save_delete", "value"),
    prevent_initial_call = True
)
def delete_scan(delete, save_delete):
    scan_options = []
    scans = []

    for name, dfn in scan_defs.items():
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
    Output("viewing", "options"),
    Input("generate_graphs", "n_clicks"),
    State("matches", "value"),
    prevent_initial_call = True
)
def generate_graphs(generate_graphs, matches):
    figures.clear()
    viewing_options = []

    # stats computed in this scan
    # TODO: decouple (just compute all?)
    stats = [
        f["type"] 
        for f in current_scan["filters"]
        if f["type"] != "settle"
    ]

    # generate, store figures and set viewing options
    for match in matches.split("\n"):
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
    Output("plots", "children"),
    Input("viewing", "value"),
    prevent_initial_call = True
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
                        Td(CInput(id = "save_delete", type = "text"))
                    ]),
                    Tr([
                        Td("name"),
                        Td(CInput(id = "name", type = "text"))
                    ]),
                    Tr([
                        Td("contract"),
                        Td(CInput(id = "contract", type = "text"))
                    ]),
                    Tr([
                        Td("type"),
                        Td(CInput(id = "type", type = "text"))
                    ]),
                    Tr([
                        Td("data_range"),
                        Td(CInput(id = "data_range", type = "text"))
                    ]),
                    Tr([
                        Td("result_limit"),
                        Td(CInput(id = "result_limit", type = "text"))
                    ]),
                    Tr([
                        Td("legs"),
                        Td(Textarea(id = "legs", rows = 5, cols = 30))
                    ]),
                    Tr([
                        Td("filters"),
                        Td([
                            Textarea(id = "filters", rows = 5, cols = 30)
                        ])
                    ]),
                    Tr([
                        Td("matches"),
                        Td(Textarea(id = "matches", rows = 10, cols = 30))
                    ]),
                    Tr([
                        Td(Button(id = "start", children = "start")),
                        Td(
                            Button(
                                id = "generate_graphs",
                                children = "generate_graphs"
                            )
                        )
                    ]),
                    Tr([
                        Td("viewing"),
                        Td(Dropdown(id = "viewing"))
                    ])
                ], id = "controls")
            ], style = { "width": 400 }),
            # plots
            Td(Div(id = "plots"), style = { "width": 800 })
        ]),
        Tr([
            # targets for callbacks with no output
            Td(id = "null0"),
            Td(id = "null1")
        ])
    ])


if __name__=="__main__":
    with open('./config.json') as fd:
        config = loads(fd.read())

        # set scan definitions and initialize layout
        opts = []

        for s in config["scans"]:
            name = s["name"]
            scan_defs[name] = s
            opts.append(
                {
                    "label": name,
                    "value": name
                }
            )

        app.layout = get_layout(opts)
        app.run_server(debug = True)