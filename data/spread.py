from enum import IntEnum
from data.contracts.contract import contract_row
from data.terms.terms import terms_row
from sys import maxsize

class spread_row(IntEnum):
    date = 0
    id = 1
    settle = 2
    change = 3
    days_listed = 4

SIDE_MAP = { "+": 1, "-": -1 }

class spread:
    def __init__(self):
        self.set_id(None)
        self.set_rows(None)

    def set_id(self, id): self.id = id
    def get_id(self): return self.id
    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows

    # e.g.: ( "+G10", "-J10")
    def set_id_by_contract(self, contracts):
        self.id = tuple(
            contract[1] + contract[0].get_id() 
            for contract in contracts 
        )

    # spread row format: ( date, id, spread, change, days_listed )
    # undefined order
    def set_rows_by_contract(self, contracts):
        id = self.get_id()
        spread_rows = {}

        for i in range(len(contracts)):
            contract = contracts[i][0]
            sign = SIDE_MAP[contracts[i][1]]
            contract_rows = contract.get_rows()
            
            for row in contract_rows:
                date = row[contract_row.date]
                settle = row[contract_row.settle] * sign
                days_listed = row[contract_row.days_listed]

                try:
                    r = spread_rows[date]
                except KeyError:
                    # [ 
                    #   accumulated spread value,
                    #   min_days_listed,
                    #   num_contracts
                    # ]
                    # per date
                    spread_rows[date] = [ 0, maxsize, 0 ]
                    r = spread_rows[date]
                
                r[0] += settle
                r[1] = min(r[1], days_listed)
                r[2] += 1

        spread_rows = [
            [ date, id, row[0], None, row[1] ]
            for date, row in spread_rows.items()
            # filter out days where not all legs were listed
            if row[2] == len(contracts)
        ]

        self.set_rows(spread_rows)
        self.set_changes()

    def set_id_by_terms(self, terms):
        self.set_id(terms["id"])

    # terms: 
    #   { 
    #       "id": [ (i, sign), ... ],
    #       "rows": [ <term_rows> ]
    #   }
    def set_rows_by_terms(self, terms):
        id = self.get_id()
        max_idx = max(id, lambda t_id: t_id[1])
        rows = []

        idx = 0
        sign = 1

        for term_set in terms["rows"]:
            if len(term_set) > max_idx:
                date = term_set[0][terms_row.date]
                settle = 0
                dl = min(term_set, lambda r: r[terms_row.date])

                for t_id in id:
                    settle += t_id[sign] * \
                        term_set[t_id[idx]][terms_row.settle]

                rows.append([ date, id, settle, None, dl ])
            

        self.set_rows(rows)
        self.set_changes()

    def set_changes(self):
        rows = self.get_rows()
        rows.sort(key = lambda x: x[spread_row.date] )

        for i in range(1, len(rows)):
            rows[i][spread_row.change] = \
            rows[i][spread_row.settle] - \
            rows[i - 1][spread_row.settle]

    def __len__(self):
        return len(self.get_rows())

    def __str__(self):
        return repr(self.id)