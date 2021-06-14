from enum import IntEnum
from data.contracts.contract import contract_row

class spread_row(IntEnum):
    __order__ = "date id spread days_listed"
    date = 0
    id = 1
    spread = 2
    days_listed = 3

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

    # spread row format: ( date, id, spread, days_listed )
    # undefined order
    def set_rows_by_contract(self, contracts):
        id = self.get_id()
        spread_rows = {}

        for i in range(len(contracts)):
            contract = contracts[i][0]
            sign = SIDE_MAP[contracts[i][1]]
            contract_rows = contract.get_rows()
            
            for row in contract_rows:
                date = row[0]
                price = row[1] * sign
                days_listed = row[2]

                try:
                    spread_row = spread_rows[date]
                except KeyError:
                    spread_rows[date] = [ 0, 0 ]
                    spread_row = spread_rows[date]
                
                spread_row[0] += price
                spread_row[1] = max(spread_row[1], days_listed)

        self.rows = [
            ( id, date, row[0], row[1] )
            for date, row in spread_rows.items()
        ]

    def set_id_by_terms(self, terms):
        pass

    def set_rows_by_terms(self, terms):
        pass

    def __str__(self):
        return repr(self.id)