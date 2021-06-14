from data.data_store import data_row
from operator import itemgetter
from datetime import datetime
from statistics import stdev, mean
from math import log
from enum import IntEnum
from numpy import polyfit

class spread_set_row(IntEnum):
        __order__ = 'date id price days_listed vol beta'
        date = 0
        id = 1
        price = 2
        days_listed = 3
        vol = 4
        beta = 5

spread_set_index = {
    "date": 0,
    "id": 1,
    "price": 2,
    "days_listed": 3,
    "vol": 4,
    "beta": 5
}

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
    def get_live(self): return self.life
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
        rows.sort(itemgetter(spread_set_row.date), reverse = True)
        
        latest_update = datetime.strptime(
            rows[0][spread_set_row.date], 
            "%Y-%m-%d"
        )
        today = datetime()
        
        live = (today - latest_update).days < self.MAX_WINDOW
        self.set_live(live)
        if (live):
            self.add_stats()
            self.init_cols()

    # add vol and beta
    def add_stats(self):
        spread_rows = self.get_rows()

        # volatility
        # x = days_listed
        # y = price volatility
        ax = {}

        for row in spread_rows:
            x = row[spread_set_row.days_listed]
            if x not in ax:
                ax[x] = []
            ax[x].append(row)
        
        for x, y in ax.items():
            try:
                sigma = stdev([ row[spread_set_row.price] for row in y ])
            except:
                # not enough points, probably
                sigma = None
            for row in y:
                row[spread_set_row.vol] = sigma
            
        # beta 
        # x = log front month return
        # y = average log spread return
        # 20 period window
        nearest = self.get_data_store().get_nearest_contract()
        y = {}
        xy = [
            # [ date, front month return, avg spread return, beta ]
            [ row[data_row.date], row[data_row.settle], None, None ] 
            for row in nearest 
        ] 

        # group spread(set) rows by date
        for row in spread_rows:
            dt = row[spread_set_row.date]
            if dt not in y:
                y[dt] = []
            y[dt].append[row]

        # calculate log returns for front month and spreads
        for i in range(len(xy)):
            current = xy[i]
            dt = current[0]
            if dt in y:
                current[2] = mean(
                    [ row[spread_set_row.settle] for row in y[dt] ]
                )
            if i > 1:
                prev = xy[i - 1]
                current[1] = log(current[1] / prev[1])
                current[2] = log(current[2] / prev[2])
        
        # first month is not valid
        xy[0][1] = None
        xy[0][2] = None

        # b =   N*sum(XY) - sum(X)sum(y)
        #       ------------------------
        #       N*sum(X^2) - sum(X)^2
        #       
        for i in range(len(xy)):
            if i < 21:
                b = None
            else:
                xy_ = 0
                x_ = 0
                y_ = 0
                x2_ = 0

                for j in range(i - 20, i):
                    current = xy[j]
                    xy_ += current[1] * current[2]
                    x_ += current[1]
                    y_ += current[2]
                    x2_ += current[1]**2

                b = (20 * xy_ - x_ * y_) / (20 * x2_ - x_**2)

            # propagate to rows
            dt = xy[0]
            for row in y[dt]:
                row[spread_set_row.beta] = b

    # after determining a live spread, need to build sorted
    # columns for rank filters
    def init_cols(self):
        rows = self.get_rows()
        cols = self.get_cols()
        for _, i in spread_set_index.items():
            cols[i] = [ row[i] for row in rows ].sort()

    # input:    ( date, ( id ), spread, days_listed )
    # output:   [ date, ( id ), spread, days_listed, vol, beta ]
    def add_spread(self, spread):
        self.set_len(self.get_len() + 1)
        rows = self.get_rows()
        spread_rows = spread.get_rows()
        processed = [
            [ 
                row[spread_set_row.date], 
                row[spread_set_row.id], 
                row[spread_set_row.price], 
                row[spread_set_row.days_listed],
                None, None 
            ] 
            for row in spread_rows
        ]
        rows.append(processed)

    def __len__(self):
        return self.get_len()