class data_store:
    
    def __init__(self, contract, range, cursor):
        self.set_cursor(cursor)
        self.set_contract(contract)
        self.set_range(range)

        self.init_rows()

    def init_rows(self):
        cursor = self.get_cursor()
        contract = self.get_contract()
        range = self.get_range()

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
            AND date BETWEEN "{range["start"]}" AND "{range["end"]}"
            ORDER BY date ASC, year ASC, month ASC;
        ''').fetchall()
    
        self.set_rows(rows)

    def set_cursor(self, cursor): self.cursor = cursor
    def get_cursor(self): return self.cursor

    def set_contract(self, contract): self.contract = contract
    def get_contract(self): return self.contract

    def set_range(self, range): self.range = range
    def get_range(self): return self.range

    def set_rows(self, rows): self.rows = rows
    def get_rows(self): return self.rows