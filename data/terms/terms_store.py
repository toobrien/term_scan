
from data.data_store import data_store
from data.terms.terms_iterator import terms_iterator
from data.terms.terms import terms_row
from data.spread import spread
from data.spread_set import spread_set

class terms_store(data_store):
    def __init__(self, contract, data_range, cursor):
        super().__init__(contract, data_range, cursor)
        self.init_terms(self.get_rows())

    # [
    #   [
    #       [ d1, s_t1, dl_t1 ],
    #       [ d1, s_t2, dl_t2 ],
    #       ...
    #   ],
    #   [
    #       [ d2, s_t1, dl_t1 ],
    #       ...
    #   ],
    #   ...
    # ]
    def init_terms(self, rows):
        cur_dt = rows[0][terms_row.date]
        terms_sets = []
        terms = []

        for i in range(len(rows)):
            cur_row = rows[i]
            if cur_row[terms_row.date] != cur_dt:
                terms_sets.append(terms)
                cur_dt = cur_row[terms_row.date]
                terms = [ cur_row ]
            else:
                terms.append[ cur_row ]
            
        if len(terms) > 0:
            terms_sets.append(terms)

        self.rows(terms_sets)

    def get_iterator(self, legs):
        return terms_iterator(legs)

    def get_spread_set(self, match):
        terms = {
            "rows": self.get_terms(),
            "match": self.get_match()
        }
        ss = spread_set(match, self)
        s = spread()

        s.set_id_by_terms(terms)
        s.set_rows_by_terms(terms)

        if len(s) > 0:
            ss.add_spread(s)
            ss.organize()
            return ss
        else:
            return None