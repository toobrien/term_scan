
from data.data_store import data_store
from data.terms import terms

class terms_store(data_store):

    def __init__(self, contract, range, cursor):
        super().__init__(contract, range, cursor)

    def get_matches(self, legs):
        return []

    def rank(self, match):
        return None