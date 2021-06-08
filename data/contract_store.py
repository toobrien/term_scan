from data.data_store import data_store
from data.contract import contract

class contract_store(data_store):

    def __init__(self, contract, range, cursor):
        super().__init__(contract, range, cursor)

    # if item in
    def __contains__(self, item):
        pass

    # []
    def __getitem__(self, key):
        pass

    # for ... in
    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if (self.i < len(self.rows)):
            curve = self.rows[self.i]
            self.i = self.i + 1
            return curve
        else:
            raise StopIteration