from data.data_store import nearest_row
from window_stats import var, avg, cov
from datetime import datetime
from enum import IntEnum
from functools import reduce
from math import sqrt
from operator import itemgetter, add
from data.spread import spread_row
from statistics import stdev, mean

class spread_set_row(IntEnum):
    date = 0
    id = 1
    settle = 2
    change = 3
    days_listed = 4
    vol = 5
    m_tick = 6
    beta = 7
    r_2 = 8

spread_set_index = {
    "date": 0,
    "id": 1,
    "settle": 2,
    "change": 3,
    "days_listed": 4,
    "vol": 5,
    "m_tick": 6,
    "beta": 7,
    "r_2": 8
}

MA_PERIODS = 30 # moving average periods
MAX_WINDOW = 5  # maximum days since latest data point for 
                # latest spread in set to be tradeable/"live"


class spread_set:

    def __init__(self, match, data_store):
        self.set_cols([ None for i in spread_set_index ])
        self.set_data_store(data_store)
        self.set_id(match)
        self.set_latest(None)
        self.set_len(0)
        self.set_live(False)
        self.set_median(None)
        self.set_rows([])


    def set_col(self, i, col): self.cols[i] = col
    def get_col(self, i): return self.cols[i]
    def set_cols(self, cols): self.cols = cols
    def get_cols(self): return self.cols
    def set_data_store(self, data_store): self.data_store = data_store
    def get_data_store(self): return self.data_store
    def set_id(self, id): self.id = id
    def get_id(self): return self.id
    def set_latest(self, latest): self.latest = latest
    def get_latest(self): return self.latest
    def set_len(self, len): self.len = len
    def get_len(self): return self.len
    def set_live(self, live): self.live = live
    def get_live(self): return self.live
    def set_median(self, median): self.median = median
    def get_median(self): return self.median
    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows


    #   - assumes more than one spread has been added
    #   - called from data_store after all spreads have been added
    def organize(self):
        # sort
        rows = self.get_rows()
        rows.sort(key = itemgetter(spread_set_row.date))

        # latest record: assume rows[0] is latest record in any
        # tradeable spread
        latest_update = datetime.strptime(
            rows[len(rows) - 1][spread_set_row.date], 
            "%Y-%m-%d"
        )
        today = datetime.now()
        live = (today - latest_update).days < MAX_WINDOW
        self.set_live(live)

        if (live):
            self.set_latest(rows[0])


#   - assumes rows sorted ascending by date in organize()
    #   - vol, beta, and r_2 are look-behind, intra-spread stats
    #   - m_tick is a look-ahead, inter-spread stat
    def add_stats(self, stats):
        spread_set_rows = self.get_rows()
        nearest = self.get_data_store().get_nearest_contract()
        spreads = {}

        # group rows by id
        for row in spread_set_rows:
            id = row[spread_set_row.id]
            if id not in spreads:
                spreads[id] = []
            spreads[id].append(row)

        # add stats to rows
        if "vol" in stats: 
            self.vol(spreads)

        if "m_tick" in stats:
            self.m_tick(spreads)

        if "beta" or "r_2" in stats:
            # y:
            #   - spread returns
            #   - { spread_id: [ [ date, return ], ... ]}
            # x:
            #   - front month returns
            #   - { date: return }
            x = {}
            for row in nearest:
                x[row[nearest_row.date]] = row[nearest_row.change]

            y = {}
            for id, rows in spreads.items():
                if id not in y:
                    y[id] = []
                y_ = y[id]
                for i in range(1, len(rows)):
                    cur = rows[i]
                    y_.append(
                        [
                            cur[spread_set_row.date], 
                            cur[spread_set_row.change]
                        ]
                    )
            if "beta" in stats: self.beta(x, y, spreads)
            if "r_2" in stats: self.r_2(x, y, spreads)
        
        # now that stats are in the rows, init their cols
        self.init_cols(stats)


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


    # beta: regression coefficient
    #   - N*sum(XY) - sum(X)sum(y)
    #     ------------------------
    #     N*sum(X^2) - sum(X)^2      
    #   - x = front month return
    #   - y = spread return
    def beta(self, x, y, spreads):
        for id, rows in y.items():
            XY = 0
            X = 0
            Y = 0
            X2 = 0
            x_rtns = []
            y_rtns = []

            for i in range(len(rows)):
                y_dt = rows[i][0]
                y_rtn = rows[i][1]
                    
                try:
                    x_rtn = x[y_dt]
                except KeyError:
                    continue

                x_rtns.append(x_rtn)
                y_rtns.append(y_rtn)

                if i > MA_PERIODS:
                    x_0 = x_rtns[i - MA_PERIODS]
                    y_0 = y_rtns[i - MA_PERIODS]

                    XY -= y_0 * x_0
                    X -= x_0
                    Y -= y_0
                    X2 -= x_0**2

                XY += y_rtn * x_rtn
                X += x_rtn
                Y += y_rtn
                X2 += x_rtn**2
                
                # spreads[id] and y[id] should be sync'd
                # e.g. spreads[id][1][date] == y[id][1][date]
                if i > MA_PERIODS:
                    b = (MA_PERIODS * XY - X * Y) / \
                        (MA_PERIODS * X2 - X**2)
                    
                    spreads[id][i][spread_set_row.beta] = b

        # TODO: average by dte here


    #   - m_tick = MA(AVG_IS(C_t * (S_t-1 - M)/ABS(C_t * (S_t-1 - M))))
    #       where: 
    #               C_t = change at time t
    #               M = median
    #               S_t-1 = settle at time t-1
    #               MA = lookahead moving average
    #               AVG_IS = intra-spread average (by days_listed)
    #   - domain is [-1, 1]
    #   - -1 means all spreads ticked away from median, 1 all spreads toward
    def m_tick(self, spreads):
        self.add_median()
        median = self.get_median()
        ticks_by_dl = {}

        # prepare ticks for aggregation
        for _, spread_rows in spreads.items():
            for i in range(1, len(spread_rows)):
                cur = spread_rows[i]
                prev = spread_rows[i - 1]

                days_listed = int(cur[spread_set_row.days_listed])

                x = cur[spread_set_row.change] * \
                    (median - prev[spread_set_row.settle])
                try:
                    x = x / abs(x)
                except ZeroDivisionError:
                    continue
                
                if days_listed not in ticks_by_dl:
                    ticks_by_dl[days_listed] = []

                ticks_by_dl[days_listed].append(x)

        # average ticks across spreads
        for dl, ticks in ticks_by_dl.items():
            if len(ticks) > 0:
                ticks_by_dl[dl] = mean(ticks)
        
        sum = 0
        dls = list(ticks_by_dl.keys())
        dls.sort()
        m_ticks = {}

        # apply moving average
        for i in range(len(dls)):
            cur_dl = dls[i]
            cur_tick = ticks_by_dl[cur_dl]
            if i >= MA_PERIODS:
                m_ticks[cur_dl] = sum / MA_PERIODS
                prev_tick = ticks_by_dl[dls[i - MA_PERIODS]]
                sum -= prev_tick
            sum += cur_tick

        # propagate to rows (for visualizing)
        rows = self.get_rows()
        for row in rows:
            dl = row[spread_set_row.days_listed]
            try:
                row[spread_set_row.m_tick] = m_ticks[dl]
            except KeyError:
                # not all days_listed has a corresponding m_tick
                continue

        # set column here instead of from rows to prevent
        # excessive duplicates
        col = [ m_tick for _, m_tick in m_ticks.items() ].sort()
        self.set_col(spread_set_row.m_tick, col)

                
    # coefficient of determination:
    #   - (COV(XY) / (STDEV(X) * STDEV(Y)))^2
    #   - x = front month returns:  [ [ dt, settle, change ], ... ]
    #   - y = spread returns:       { id: [ spread_set_row, ... ], ... }
    def r_2(self, x, y, spreads):
        for id, rows in y.items():
            x_rtns = []
            y_rtns = []
            x_var = var(MA_PERIODS)
            y_var = var(MA_PERIODS)
            xy_cov = cov(MA_PERIODS)

            for i in range(len(rows)):        
                y_dt = rows[i][0]
                y_rtn = rows[i][1]

                try:
                    x_rtn = x[y_dt]
                except KeyError:
                    continue
                
                x_rtns.append(x_rtn)
                y_rtns.append(y_rtn)

                x_sigma = sqrt(x_var.next(x_rtns, i))
                y_sigma = sqrt(y_var.next(y_rtns, i))

                if x_sigma <= 0 or y_sigma <=0:
                    continue

                cov_xy = xy_cov(x_rtns, y_rtns, i)
                r_2 = (cov_xy / (x_sigma * y_sigma))**2

                if i >= MA_PERIODS:
                    spreads[id][i][spread_set_row.r_2] = r_2
            
        # TODO: average by dte here

    #   - columns used for rank filters
    #   - only computed for live spreads
    #   - inter-spread stats initialized elsewhere
    def init_cols(self, indicies):
        rows = self.get_rows()
        cols = self.get_cols()

        for idx in indicies:
            if idx == "m_tick":
                # set in m_tick() instead
                continue

            i = spread_set_index[idx]
            
            cols[i] = [ 
                row[i] for row in rows
                if row[i] is not None
            ]
            cols[i].sort(key = lambda x: float(x))


    def add_median(self):
        if self.get_col(spread_set_index["settle"]) == None:
            self.init_cols(["settle"])
            
        settlements = self.get_col(spread_set_row.settle)
        l = len(settlements)
        mid = l // 2

        if l % 2 == 0:
            self.set_median((settlements[mid] + settlements[mid - 1]) / 2)
        else:
            self.set_median(settlements[mid])


    # input:    spread_row
    # output:   spread_set_row
    def add_spread(self, spread):
        self.set_len(self.get_len() + 1)
        rows = self.get_rows()
        spread_rows = spread.get_rows()

        for row in spread_rows:
            rows.append(
                [
                    row[spread_row.date], 
                    row[spread_row.id], 
                    row[spread_row.settle],
                    row[spread_row.change],
                    row[spread_row.days_listed],
                    None,   # vol
                    None,   # m_tick
                    None,   # beta
                    None    # r_2
                ]
            )

    def __len__(self):
        return self.get_len()