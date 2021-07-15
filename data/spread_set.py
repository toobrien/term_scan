from data.data_store import nearest_row
from window_stats import var, avg, cov
from datetime import datetime
from enum import IntEnum
from math import sqrt
from operator import itemgetter
from data.spread import spread_row
from statistics import mean, stdev

class spread_set_row(IntEnum):
    date = 0
    agg_id = 1
    plot_id = 2
    settle = 3
    change = 4
    days_listed = 5
    vol = 6
    m_tick = 7
    beta = 8
    r_2 = 9

spread_set_index = {
    "date": 0,
    "agg_id": 1,
    "plot_id": 2,
    "settle": 3,
    "change": 4,
    "days_listed": 5,
    "vol": 6,
    "m_tick": 7,
    "beta": 8,
    "r_2": 9
}

MA_PERIODS = 30 # moving average periods
MAX_WINDOW = 5  # maximum days since latest data point for 
                # latest spread in set to be tradeable/"live"


class spread_set:

    def __init__(self, match, data_store):
        self.set_stats({})
        self.set_data_store(data_store)
        self.set_id(match)
        self.set_latest(None)
        self.set_len(0)
        self.set_live(False)
        self.set_rows([])


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
    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows
    def set_stats(self, stats_dict): self.stats = stats_dict
    def set_stat(self, stat, stat_dict): self.stats[stat] = stat_dict
    def get_stat(self, stat): return self.stats[stat]


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
        dl = {}

        # group rows by days_listed
        for row in spread_set_rows:
            x = int(row[spread_set_row.days_listed])
            if x not in dl:
                dl[x] = []
            dl[x].append(row)

        # mandatory: settlement median is used in various places
        self.add_stat("settle", dl)
        try: stats.remove("settle")
        except: pass

        # group rows by agg_id
        # agg_id allows stats to be computed differently
        # for contract- and terms- style spreads
        for row in spread_set_rows:
            agg_id = row[spread_set_row.agg_id]
            if agg_id not in spreads:
                spreads[agg_id] = []
            spreads[agg_id].append(row)

        # add stats to rows
        if "vol" in stats: 
            self.vol(spreads)

        if "m_tick" in stats:
            self.m_tick(spreads)

        if "beta" or "r_2" in stats:
            # y:
            #   - spread returns
            #   - { agg_id: [ [ date, return ], ... ]}
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
        
        # rows are fully populated, so add summary statistics
        for stat in stats: self.add_stat(stat, dl)


    # creates summary statistics
    # make sure individual rows are populated first
    # stat: "<name of statistic>"
    # dl:   { days_listed: [ row_0, row_1, ..., row_n ] }
    def add_stat(self, stat, dl):
        idx = spread_set_index[stat]
        rows = self.get_rows()
        vals = sorted(
            [ 
                row[idx] for row in rows
                if row[idx] is not None
            ],
            key = lambda x: float(x)
        )
        
        # time series
        # x = days_listed, y = avg value
        # [ [ x0, y0 ], ..., [ xn, yn ] ] 
        stat_rows = []
        for x, rows in dl.items():
            spread_vals = [ 
                    row[idx] for row in rows 
                    if row[idx] is not None
                ]   
            if len(spread_vals) > 0:
                stat_rows.append([x, mean(spread_vals)])
        stat_rows.sort(key = lambda x: x[1] )

        # mean
        avg = mean(vals)

        # median
        mid = len(stat_rows) // 2
        if len(stat_rows) % 2 == 0:
            median = \
                (
                    stat_rows[mid - 1][1] +\
                    stat_rows[mid][1]
                ) / 2
        else:
            median = stat_rows[mid][1]
        
        # stdev
        sigma = stdev(vals)

        self.set_stat(
            stat, 
            {
                "rows": stat_rows,
                "mean": avg,
                "median": median,
                "stdev": sigma
            }
        )


    # price volatility
    def vol(self, spreads):
        for _, rows in spreads.items():
            x = [ row[spread_set_row.settle] for row in rows ]
            x_var = var(MA_PERIODS)
            for i in range(len(rows)):
                sigma = sqrt(max(x_var.next(x, i), 0))
                if i >= MA_PERIODS:
                    rows[i][spread_set_row.vol] = sigma


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
                if i >= MA_PERIODS:
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
        median = self.get_stat("settle")["median"]
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

                x_sigma = sqrt(max(x_var.next(x_rtns, i), 0))
                y_sigma = sqrt(max(y_var.next(y_rtns, i), 0))

                if x_sigma <= 0 or y_sigma <=0:
                    continue

                cov_xy = xy_cov.next(x_rtns, y_rtns, i)
                r_2 = (cov_xy / (x_sigma * y_sigma))**2

                if i >= MA_PERIODS:
                    # filter outliers
                    if r_2 <= 1:
                        spreads[id][i][spread_set_row.r_2] = r_2


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
                    row[spread_row.agg_id],
                    row[spread_row.plot_id],
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