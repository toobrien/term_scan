
from data.data_store import data_store
from data.terms.terms_iterator import terms_iterator
from data.terms.terms import terms
from data.spread import spread
from data.spread_set import spread_set

class terms_store(data_store):
    def __init__(self, contract, range, cursor):
        super().__init__(contract, range, cursor)

    def get_iterator(self, legs):
        return terms_iterator(legs)

    def calculate_spreads(self, match):
        ss = spread_set(match)

        return ss