from data.data_store import data_row
from operator import itemgetter
from datetime import datetime
from statistics import stdev, mean
from math import sqrt
from json import dumps
from enum import IntEnum

class spread_set_row(IntEnum):
        date = 0
        id = 1
        settle = 2
        days_listed = 3
        vol = 4
        beta = 5

spread_set_index = {
    "date": 0,
    "id": 1,
    "settle": 2,
    "days_listed": 3,
    "vol": 4,
    "beta": 5
}

BETA_PERIODS = 30

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
            self.add_stats()
            self.init_cols()

    # add vol and beta
    def add_stats(self):
        spread_rows = self.get_rows()

        # vol
        # ----------
        # x = days_listed
        # y = settlement volatility
        ax = {}

        for row in spread_rows:
            dl = row[spread_set_row.days_listed]
            if dl not in ax:
                ax[dl] = []
            ax[dl].append(row)
        
        for dl, rows in ax.items():
            try:
                sigma = sqrt(
                    stdev(
                        [ row[spread_set_row.settle] for row in rows ]
                    )
                )
            except:
                # not enough points, probably
                sigma = None
            for row in rows:
                row[spread_set_row.vol] = sigma
            
        # beta
        # ----------
        # x = front month return
        # y = average spread return
        # 1. compute moving average of length BETA_PERIODS
        # 2. average by days_listed
        nearest = self.get_data_store().get_nearest_contract()
        
        # date: [ spread_rows ]
        y = {}

        # [ date, front month settle, spread settle ]
        xys = [
            [ row[data_row.date], row[data_row.settle], None ] 
            for row in nearest 
        ]

        # [ date, front month return, spread return ]
        xyr = []

        # group spread_set rows by date
        for row in spread_rows:
            dt = row[spread_set_row.date]
            if dt not in y:
                y[dt] = []
            y[dt].append(row)

        # add spread settlements to xys
        for i in range(len(xys)):
            current = xys[i]
            dt = current[0]
            if dt in y:
                current[2] = mean(
                    [ row[spread_set_row.settle] for row in y[dt] ]
                )

        # compute returns
        # [ date, front_month_return, spread_return]
        for i in range(1, len(xys)):
            current = xys[i]
            prev = xys[i - 1]
            if prev[2] and current[2]:
               xyr.append(
                   [
                        current[0],
                        #(current[1] - prev[1]) / prev[1],
                        #(current[2] - prev[2]) / prev[2]
                        current[1] - prev[1],
                        current[2] - prev[2]
                   ]
               )

        # compute beta
        # b =   N*sum(XY) - sum(X)sum(y)
        #       ------------------------
        #       N*sum(X^2) - sum(X)^2
        #       
        for i in range(len(xyr)):
            if i < BETA_PERIODS:
                b = None
            else:
                XY = 0
                X = 0
                Y = 0
                X2 = 0

                for j in range(i - BETA_PERIODS, i):
                    current = xyr[j]
                    XY += current[1] * current[2]
                    X += current[1]
                    Y += current[2]
                    X2 += current[1]**2

                b = (20 * XY - X * Y) / (20 * X2 - X**2)

            # propagate to rows
            dt = xyr[i][0]
            for row in y[dt]:
                row[spread_set_row.beta] = b

        # average by days_listed -- reuse ax
        for dl, rows in ax.items():
            avg_b = 0.
            num_rows = len(rows)
            
            for i in range(num_rows):
                b = rows[i][spread_set_row.beta]
                if (b): avg_b += b
            
            avg_b /= num_rows

            for row in rows:
                row[spread_set_row.beta] = avg_b


    # columns used for rank filters
    # only computed for live spreads
    def init_cols(self):
        rows = self.get_rows()
        cols = self.get_cols()
        for _, i in spread_set_index.items():
            cols[i] = [ row[i] for row in rows ]

        # filter "None" if needed
        # remove duplicates
        # shouldn't hurt ranking because *reasons* (?)
        cols[spread_set_row.days_listed] = list(set(
            x for x in cols[spread_set_row.days_listed]
        ))
        cols[spread_set_row.vol] = list(set(
            x for x in cols[spread_set_row.vol] if x is not None
        ))
        cols[spread_set_row.beta] = list(set(
            x for x in cols[spread_set_row.beta] if x is not None
        ))

        # sort
        for _, i in spread_set_index.items():
            cols[i].sort()
            print(dumps(cols[i], indent = 2))

        exit()

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
                    None, None
                ]
            )

    def __len__(self):
        return self.get_len()