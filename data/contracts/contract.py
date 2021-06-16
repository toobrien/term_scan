from enum import IntEnum

class contract_row(IntEnum):
    date = 0
    settle = 1
    days_listed = 2

class contract:
    def __init__(self, id, month, year):
        self.set_id(id)
        self.set_month(month)
        self.set_year(int(year))
        self.set_rows([])
    
    def set_month(self, month): self.month = month
    def get_month(self): return self.month

    def set_year(self, year): self.year = year
    def get_year(self): return self.year

    def set_id(self, id): self.id = id
    def get_id(self): return self.id

    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows

    def add_row(self, row):
        self.get_rows().append(row)

    def __str__(self):
        return self.id

    def __repr__(self):
        return self.id