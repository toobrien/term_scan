from enum import IntEnum

class data_row(IntEnum):
    __order__ = "name month year date settle days_listed"
    name = 0
    month = 1
    year = 2
    date = 3
    settle = 4
    days_listed = 5

class data_store:
    def __init__(self, contract, range, cursor):
        self.set_cursor(cursor)
        self.set_contract(contract)
        self.set_data_range(range)

        self.init_rows()

    def set_cursor(self, cursor): self.cursor = cursor
    def get_cursor(self): return self.cursor
    def set_contract(self, contract): self.contract = contract
    def get_contract(self): return self.contract
    def set_data_range(self, data_range): self.data_range = data_range
    def get_data_range(self): return self.data_range
    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows
    def set_nearest_contract(self, contract): self.nearest_contract = contract
    def get_nearest_contract(self): return self.nearest_contract

    def init_nearest_contract(self):
        rows = self.get_rows()
        current_date = None
        nearest_contract = [ rows[0] ]

        for row in rows:
            if row[data_row.date] != current_date:
                nearest_contract.append(row)
                current_date = row[data_row.date]
        
        self.set_nearest_contract(nearest_contract)

    def init_rows(self):
        cursor = self.get_cursor()
        contract = self.get_contract()
        data_range = self.get_data_range()

        rows = cursor.execute(f'''
            SELECT DISTINCT
                name,
                month,
                year,
                date,
                settle,
                julianday(date) - julianday(from_date) AS days_listed
            FROM ohlc INNER JOIN metadata USING(contract_id)
            WHERE name = "{contract}"
            AND date BETWEEN "{data_range[0]}" AND "{data_range[1]}"
            ORDER BY date ASC, year ASC, month ASC;
        ''').fetchall()
    
        self.set_rows(rows)
        self.init_nearest_contract()