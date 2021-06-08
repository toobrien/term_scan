from data.contract_store import contract_store
from data.terms_store import terms_store
from result import result

class scan:
    
    def __init__(self, scan_def, cursor):
        self.set_name(scan_def["name"])
        self.set_contract(scan_def["contract"])
        self.set_result(result(self.name, self.contract))

        params = scan_def["params"]
        self.set_type(params["type"])
        self.set_filters(params["filters"])
        self.set_legs(params["legs"])

        self.init_range(self.filters)
        self.init_data_store(cursor)
        
    def set_range(self, range): self.range = range
    def get_range(self): return self.range

    def set_data_store(self, data): self.data = data
    def get_data_store(self): return self.data
    
    def set_name(self, name): self.name = name
    def get_name(self): return self.name
    
    def set_contract(self, contract): self.contract = contract
    def get_contract(self): return self.contract

    def set_result(self, result): self.result = result
    def get_result(self): return self.result

    def set_type(self, type): self.type = type
    def get_type(self): return self.type

    def set_filters(self, filters): self.filters = filters
    def get_filters(self): return self.filters

    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs

    def init_data_store(self, cursor):
        data_store = None
        type = self.get_type()

        contract = self.get_contract()
        range = self.get_range()

        if type == "calendar":
            data_store = contract_store(contract, range, cursor)
        elif type == "sequence":
            data_store = terms_store(contract, range, cursor)
        
        self.set_data_store(data_store)
        
    def init_range(self, filters):
        range = {
            "start": "2018-01-01",
            "end": "2035-01-01"
        }

        for filter in filters:
            if filter["type"] == "date":
                range["start"] = filter["range"][0]
                range["end"] = filter["range"][1]

        self.set_range(range)
                

    def execute(self):
        result = self.get_result()
        data_store = self.get_data_store()
        
        for row in data_store.get_rows():
            print(row)
        
        return result
