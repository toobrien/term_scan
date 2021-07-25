from data.contracts.contract_store import contract_store
from data.terms.terms_store import terms_store
from data.spread_set import spread_set_index
from data.spread_set import spread_set_row
from datetime import datetime

class scan:
    def __init__(self, scan_def, cursor):
        self.set_name(scan_def["name"])
        self.set_contract(scan_def["contract"])
        self.set_type(scan_def["type"])
        self.set_data_range(scan_def["data_range"])
        self.set_result_limit(scan_def["result_limit"])
        self.set_legs(scan_def["legs"])
        self.set_filters(scan_def["filters"])

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

        i = spread_set_index[type]
        stats = spread_set.get_stat(type)

        latest = spread_set.get_latest()
        val = latest[i]

        in_rng = False 
            
        for j in range(len(rng)):
            lower = rng[j][0]
            upper = rng[j][1]

            if mode == "std":
                lower = stats["median"] + lower * stats["std"]
                upper = stats["median"] + upper * stats["std"]

            in_rng =    in_rng or \
                        (
                            val >= lower and
                            val <= upper
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

        print(f"starting scan: {self.get_name()}")
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
                agg_id = latest[spread_set_row.agg_id]
                if not agg_id in seen:
                    seen.add(agg_id)
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
                    results.append(
                        {
                            "match": match, 
                            "data": spread_set
                        }
                    )

            if (result_limit and len(results) >= result_limit): break

        print("elapsed:", datetime.now() - start)

        if (result_limit):
            response["results"] = results[:result_limit]

        return response