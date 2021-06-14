class terms_iterator:
    def __init__(self, legs):
        self.set_legs(legs)

    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs