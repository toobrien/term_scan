from data.contracts.contract_store import contract_store
from data.terms.terms_store import terms_store
from data.spread_set import SPREAD_INDEX
from bisect import bisect_left

class scan:
    
    def __init__(self, scan_def, cursor):
        self.set_name(scan_def["name"])
        self.set_contract(scan_def["contract"])

        params = scan_def["params"]
        self.set_type(params["type"])
        self.set_filters(params["filters"])
        self.set_legs(params["legs"])
        self.set_data_range(params["data_range"])
        self.set_result_limit(params["result_limit"])

        self.init_data_store(cursor)
        
    def set_data_range(self, data_range): self.data_range = data_range
    def get_data_range(self): return self.data_range
    def set_data_store(self, data): self.data = data
    def get_data_store(self): return self.data
    def set_name(self, name): self.name = name
    def get_name(self): return self.name
    def set_contract(self, contract): self.contract = contract
    def get_contract(self): return self.contract
    def set_type(self, type): self.type = type
    def get_type(self): return self.type
    def set_filters(self, filters): self.filters = filters
    def get_filters(self): return self.filters
    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs
    def set_result_limit(self, lim): self.result_limit = lim
    def get_result_limit(self): return self.result_limit

    def init_data_store(self, cursor):
        data_store = None
        type = self.get_type()

        contract = self.get_contract()
        data_range = self.get_data_range()

        if type == "calendar":
            data_store = contract_store(contract, data_range, cursor)
        elif type == "sequence":
            data_store = terms_store(contract, data_range, cursor)
        
        self.set_data_store(data_store)

    def check_filter(filter, spread_set):
        latest = spread_set.get_latest()
        type = filter["type"]
        mode = filter["mode"]
        range = filter["range"]
        data = spread_set.column(type)
        i = SPREAD_INDEX[type]
        val = latest[i]
        in_rng = False

        if mode == "rank": 
            val = bisect_left(val, data) / len(data)
        
        for j in len(range):
            in_rng =    in_rng or \
                        latest[i] >= range[j][0] and \
                        latest[i] <= range[j][1]
            if (in_rng):
                return val
        
        return None

    def execute(self):
        filters = self.get_filters()
        response = {
            "name": self.get_name(),
            "contract": self.get_contract(),
            "results": []
        }
        results = response["results"]
        result_limit = self.get_result_limit()
        
        data_store = self.get_data_store()
        it = data_store.get_iterator(self.get_legs())

        for match in it:
            spread_set = data_store.calculate_spreads(match)

            if (spread_set and spread_set.get_live()):
                spread_set.init_columns()
                result = {}
                pass_all = True

                for fn in filters:
                    val = self.check_filter(filters[fn], spread_set)

                    if (not val):
                        # filters are AND'd, ranges are OR'd
                        pass_all = False
                        break
                    else:
                        result[fn] = val

                if (pass_all): 
                        results.append(result)

            if (result_limit and len(results) >= result_limit): break
        
        if (result_limit):
            response["results"] = results[:result_limit]

        return response