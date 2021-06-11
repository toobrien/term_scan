
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

    def __subtract__(self, other):
        return 12 * (self.year - other.year) + self.month - other.month

    def __eq__(self, other):
        return  self.id == other.id 

    def __lt__(self, other):
        return  self.year < other.year or \
                (
                    self.year == other.year and
                    self.month < other.month
                )

    def __gt__(self, other):
        return  self.year > other.year or \
                (
                    self.year == other.year and
                    self.month > other.month
                )