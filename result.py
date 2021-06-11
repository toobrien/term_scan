class result:

    def __init__(self, contract, id):
        self.set_contract(contract)
        self.set_id(id)
        self.set_legs(None)
    
    def set_id(self, id): self.id = id
    def get_id(self): return self.id

    def set_contract(self, contract): self.contract = contract
    def get_contract(self): return self.contract

    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs