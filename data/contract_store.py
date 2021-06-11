from data.data_store import data_store
from data.contract import contract
from data.contract_iterator import contract_iterator

class contract_store(data_store):

    def __init__(self, contract, range, cursor):
        super().__init__(contract, range, cursor)
        self.set_contracts([])
        self.init_contracts()
    
    def set_contracts(self, contracts): self.contracts = contracts
    def get_contracts(self): return self.contracts
    
    def init_contracts(self):
        contracts = self.get_contracts()
        rows = self.get_rows()

        # ('LN', 'V', '2022', '2021-06-08', 80.6, float)
        for row in rows:
            id = row[1] + row[2:]
            
            if id not in contracts:
                contracts[id] = contract(id, row[1], row[2])
        
            contracts[id].add(row[3:])

        self.set_contracts(contracts)

    def get_iterator(legs):
        return contract_iterator(legs)

    def rank(self, match):
        return None