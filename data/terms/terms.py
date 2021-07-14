from enum import IntEnum

class terms_row(IntEnum):
    date = 0
    settle = 1
    days_listed = 2

# not used
'''
class terms:

    def __init__(self, id, rows):
        self.set_id(id)
        self.set_rows(rows)

    def set_id(self, id): self.id = id
    def get_id(self): return self.id
    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows
'''