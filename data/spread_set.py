from data.data_store import data_row
from operator import itemgetter
from datetime import datetime
from statistics import stdev, mean
from math import sqrt
from enum import IntEnum
from functools import reduce
from operator import add

class spread_set_row(IntEnum):
    date = 0
    id = 1
    settle = 2
    days_listed = 3
    vol = 4
    beta = 5
    r_2 = 6

spread_set_index = {
    "date": 0,
    "id": 1,
    "settle": 2,
    "days_listed": 3,
    "vol": 4,
    "beta": 5,
    "r_2": 6
}

MA_PERIODS = 30

class spread_set:
    # maximum days since latest data point for 
    # latest spread in set to be tradeable/"live"
    MAX_WINDOW = 5

    def __init__(self, match, data_store):
        self.set_id(match)
        self.set_data_store(data_store)
        self.set_rows([])
        self.set_cols([ None for i in spread_set_index ])
        self.set_len(0)
        self.set_live(False)
        self.set_latest(None)

    def set_id(self, id): self.id = id
    def get_id(self): return self.id
    def set_data_store(self, data_store): self.data_store = data_store
    def get_data_store(self): return self.data_store
    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows
    def set_len(self, len): self.len = len
    def get_len(self): return self.len
    def set_live(self, live): self.live = live
    def get_live(self): return self.live
    def set_latest(self, latest): self.latest = latest
    def get_latest(self): return self.latest
    def set_cols(self, cols): self.cols = cols
    def get_cols(self): return self.cols
    def set_col(self, i, col): self.cols[i] = col
    def get_col(self, i): return self.cols[i]

    # after all spreads are added, sort descending by 
    # date to see if the at least one spread in this 
    # set is still tradeable, or "live".
    #
    # assumes first row holds the latest data for the 
    # tradeable spread in this set. these data are
    # used for filter comparisons.
    def sort_rows(self):
        rows = self.get_rows()
        rows.sort(
            key = itemgetter(spread_set_row.date), 
            reverse = True
        )
        
        latest_update = datetime.strptime(
            rows[0][spread_set_row.date], 
            "%Y-%m-%d"
        )
        today = datetime.now()
        
        live = (today - latest_update).days < self.MAX_WINDOW
        self.set_live(live)
        if (live):
            self.set_latest(rows[0])
            self.add_stats()
            self.init_cols()

    def get_returns(self, nearest, spreads):
        x = {}  # front month returns:  { date: return }
        y = {}  # spread returns:       { id: [ [ date, return ], ... ] }
        
        # x
        for i in range(1, len(nearest)):
            row = nearest[i]
            rtn =   row[data_row.settle] - \
                    nearest[i - 1][data_row.settle]
            dt = row[data_row.date]
            if dt not in x:
                x[dt] = rtn

        # y
        for id, rows in spreads.items():
            if id not in y:
                y[id] = {}
            y_ = y[id]
            for i in range(1, len(rows)):
                cur = rows[i]
                prev = rows[i] - 1
                dt = cur[spread_set_row.date]
                y_.append(
                    [
                        dt,
                        cur[spread_set_row.settle] -
                        prev[spread_set_row.settle]
                    ]
                )
            y_.insert(0, [])

        return (x, y)


    # x = front month return
    # y = spread return
    def beta(self, spreads, nearest):
        x, y = self.get_returns(nearest, spreads)

        # b =   N*sum(XY) - sum(X)sum(y)
        #       ------------------------
        #       N*sum(X^2) - sum(X)^2
        #       
        for id, rows in y.items():
            for i in range(1 + MA_PERIODS, len(rows)):
                XY = 0
                X = 0
                Y = 0
                X2 = 0

                for j in range(i - MA_PERIODS, i):
                    y_dt = rows[j][0]
                    y_rtn = rows[j][1]
                    
                    try:
                        x_rtn = x[y_dt]
                    except KeyError:
                        continue

                    XY += y_rtn * x_rtn
                    X += x_rtn
                    Y += y_rtn
                    X2 += x_rtn**2

                b = (MA_PERIODS * XY - X * Y) / \
                    (MA_PERIODS * X2 - X**2)
                
                # spreads[id] and y[id] should be sync'd
                # e.g. spreads[id][1][date] == y[id][1][date]
                spreads[id][j][spread_set_row.beta] = b
                
    # coefficient of determination:
    # x = front month returns
    # y = spread returns
    def r_2(self, spreads, nearest):
        x, y = self.get_returns(nearest, spreads)

        # r_2 = (COV(XY) / (STDEV(X) * STDEV(Y)))^2
        for id, rows in y.items():
            for i in range(1 + MA_PERIODS, len(rows)):
                x_ = []
                y_ = []
                
                for j in range(i - MA_PERIODS, i):
                    y_dt = rows[j][0]
                    y_rtn = rows[j][1]

                    try:
                        x_rtn = x[y_dt]
                    except KeyError:
                        continue
                
                    x_.append(x_rtn)
                    y_.append(y_rtn)
                
                x_mean = mean(x_)
                y_mean = mean(y_)
                x_sigma = stdev(x_)
                y_sigma = stdev(y_)
                cov_xy = reduce(
                    add, 
                    [ 
                        (x_[i] - x_mean) * (y_[i] - y_mean)
                        for i in range(len(x_))
                    ]
                ) / len(x_)

                r_2 = (cov_xy / (x_sigma * y_sigma))**2

            spreads[id][j][spread_set_row.r_2] = r_2

    # price volatility
    def vol(self, spreads):
        for _, rows in spreads.items():
            for i in range(MA_PERIODS, len(rows)):
                rng = rows[i - MA_PERIODS:i]
                try:
                    sigma = sqrt(
                        stdev(
                            [ 
                                row[spread_set_row.settle] 
                                for row in rng
                            ]
                        )
                    )
                except:
                    # not enough points, probably
                    sigma = None

                for row in rng:
                    row[spread_set_row.vol] = sigma

    def add_stats(self):
        spread_rows = self.get_rows()
        nearest = self.get_data_store().get_nearest_contract()
        spreads = {}

        # group by contract, already sorted by date
        for row in spread_rows:
            id = row[spread_set_row.id]
            if id not in spreads:
                spreads[id] = []
            spreads[id].append(row)

        # add stats to rows via ax
        self.vol(spreads)
        self.beta(spreads, nearest)
        self.r_2(spreads, nearest)
        
    # columns used for rank filters
    # only computed for live spreads
    def init_cols(self):
        rows = self.get_rows()
        cols = self.get_cols()
        for _, i in spread_set_index.items():
            cols[i] = [ row[i] for row in rows ]

        # filter "None"
        for idx in [ 
            spread_set_row.days_listed,
            spread_set_row.vol,
            spread_set_row.beta,
            spread_set_row.r_2
        ]:
            cols[idx] = list(x for x in cols[idx] if x is not None)

        # sort
        for _, i in spread_set_index.items():
            cols[i].sort()
            #print(dumps(cols[i], indent = 2))

        #exit()

    # input (spread_row):    
    #   ( date, ( id ), spread, days_listed )
    # output (spread_set_row):   
    #   [ date, ( id ), spread, days_listed, vol, beta ]
    def add_spread(self, spread):
        self.set_len(self.get_len() + 1)
        rows = self.get_rows()
        spread_rows = spread.get_rows()

        for row in spread_rows:
            rows.append(
                [
                    row[spread_set_row.date], 
                    row[spread_set_row.id], 
                    row[spread_set_row.settle], 
                    row[spread_set_row.days_listed],
                    None,   # vol
                    None,   # beta
                    None    # r_2
                ]
            )

    def __len__(self):
        return self.get_len()