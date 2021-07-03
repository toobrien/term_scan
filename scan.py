from data.contracts.contract_store import contract_store
from data.terms.terms_store import terms_store
from data.spread_set import spread_set_index
from data.spread_set import spread_set_row
from bisect import bisect_left
from datetime import datetime

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

    def check_filter(self, filter, spread_set):
        type = filter["type"]
        mode = filter["mode"]
        rng = filter["range"]

        latest = spread_set.get_latest()
        i = spread_set_index[type]
        data = spread_set.get_col(i)
        val = latest[i]
        in_rng = False

        if mode == "percentile": 
            val = bisect_left(data, val) / len(data)
        
        for j in range(len(rng)):
            in_rng =    in_rng or \
                        (
                            val >= rng[j][0] and
                            val <= rng[j][1]
                        )
            if (in_rng):
                return val
        
        return None

    def execute(self):
        filters = self.get_filters()
        response = {
            "name":     self.get_name(),
            "contract": self.get_contract(),
            "results":  []
        }
        results = response["results"]
        result_limit = self.get_result_limit()
        stats = [ filter["type"] for filter in filters ]
        data_store = self.get_data_store()
        it = data_store.get_iterator(self.get_legs())
        seen = set()

        start = datetime.now()

        for match in it:
            spread_set = data_store.get_spread_set(match)

            #print(match)

            if (spread_set and spread_set.get_live()):
                spread_set.add_stats(stats)
                latest = spread_set.get_latest()

                # could remove duplicates in 
                # data_store.calculate_spreads
                # but doing it here instead
                id = latest[spread_set_row.id]
                if not id in seen:
                    seen.add(id)
                else: 
                    continue

                # check filters
                # filters are AND'd, ranges are OR'd
                pass_all = True

                for f in filters:
                    val = self.check_filter(f, spread_set)

                    if (not val):
                        pass_all = False
                        break
                    else:
                        pass

                if (pass_all):
                    results.append((match, id))

            if (result_limit and len(results) >= result_limit): break

        print("elapsed:", datetime.now() - start)

        if (result_limit):
            response["results"] = results[:result_limit]

        return response