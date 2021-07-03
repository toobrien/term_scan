from data.data_store import data_store, data_row
from data.contracts.contract import contract
from data.contracts.contract_iterator import contract_iterator
from data.domain import MONTH_I2A, SIDE_MAP
from data.spread import spread
from data.spread_set import spread_set

class contract_store(data_store):
    def __init__(self, contract, data_range, cursor):
        super().__init__(contract, data_range, cursor)
        self.set_contracts({})
        self.init_contracts()
        self.init_year_range(data_range)
        self.skipped = 0
            
    def set_contracts(self, contracts): self.contracts = contracts
    def get_contracts(self): return self.contracts
    def set_year_range(self, year_range): self.year_range = year_range
    def get_year_range(self): return self.year_range

    def init_year_range(self, data_range):
        self.set_year_range(
            [   
                year for year in 
                range(
                    int(data_range[0][:4]), 
                    int(data_range[1][:4]) + 1
                ) 
            ]
        )

    def get_iterator(self, legs):
        return contract_iterator(legs)

    def init_contracts(self):
        contracts = self.get_contracts()
        rows = self.get_rows()

        for row in rows:
            id = row[data_row.month] + row[data_row.year][2:]
            
            if id not in contracts:
                contracts[id] = contract(
                    id, 
                    row[data_row.month], 
                    row[data_row.year]
                )

            contracts[id].add_row(row[data_row.date:])

        self.set_contracts(contracts)

    # ((1, 1, "A"), 2020) => ("F21", "+")
    def bind(self, leg, base_year):
        return (
            MONTH_I2A[leg[0]] + str(base_year % 100 + leg[1]), 
            SIDE_MAP[leg[2]]
        )

    def get_spread_set(self, match):
        contracts = self.get_contracts()
        year_range = self.get_year_range()
        ss = spread_set(match, self)

        for year in year_range:
            bound_matches = [ self.bind(leg, year) for leg in match ]
            valid_matches = None

            try:
                # (<contract_obj>, "+")
                valid_matches = [
                    ( contracts[bound[0]], bound[1] )
                    for bound in bound_matches
                ]
            except KeyError:
                # after binding, at least one match is not a valid contract
                continue

            s = spread()
            s.set_id_by_contract(valid_matches)
            s.set_rows_by_contract(valid_matches)
            
            if len(s) > 0:
                ss.add_spread(s)

        if len(ss) > 0:
            ss.organize()
            return ss
        else: 
            return None
                
