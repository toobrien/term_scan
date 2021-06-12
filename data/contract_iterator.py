class contract_iterator:
    MONTH_DOMAIN = {
        "F": 0,
        "G": 1,
        "H": 2,
        "J": 3,
        "K": 4,
        "M": 5,
        "N": 6,
        "Q": 7,
        "U": 8,
        "V": 9,
        "X": 10,
        "Z": 11
    }
    # year domain = max contracts listed at one time
    YEAR_DOMAIN = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    SIDE_DOMAIN = ('A', 'B')

    def __init__(self, legs):
        self.set_legs(legs)

    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs

    def set_its(self, its): self.its = its
    def get_its(self): return self.its

    def in_range(self, cur_vals, m_rng, y_rng):
        return  cur_vals["m"] <= m_rng[1] and \
                cur_vals["m"] <= self.MONTH_DOMAIN["Z"] and \
                cur_vals["y"] <= y_rng[1] and \
                cur_vals["y"] <= self.YEAR_DOMAIN[-1]

    def init_it(self, cur, prev):
        # sets cur's range and current values by 
        # binding the initializer values. e.g.:
        # 
        # prev current month:           1
        # cur month initializer:        ("+2", "V")
        #
        # will result in:
        #
        # cur current month:            3
        # cur range:                    (3, 9)
        cur_vals = cur["current"]
        m_rng = cur["range"]["m"]
        m_ini = cur["init"]["m"]
        y_rng = cur["range"]["y"] 
        y_ini = cur["init"]["y"]

        # bind range
        for i in (0,1):
            if "+" in m_ini[i]:
                m_rng[i] = prev["current"]["m"] + int(m_ini[i][1:])
            else:
                m_rng[i] = self.MONTH_DOMAIN[m_ini[i]]
            if "+" in y_ini[i]:
                y_rng[i] = prev["current"]["y"] + int(y_ini[i][1:])
            else:
                y_rng[i] = int(y_ini[i])
            
        # initialize current month, year
        cur_vals["m"] = m_rng[0]
        cur_vals["y"] = y_rng[0]

        # validate range and domain
        return  self.in_range(cur_vals, m_rng, y_rng)

    def increment_it(self, it):        
        cur = it["current"]
        rng = it["range"]

        if cur["m"] < rng["m"][1]:
            cur["m"] += 1
        elif cur["y"] < rng["y"][1]:
            cur["m"] = rng["m"][0]
            cur["y"] += 1
        else:
            return False

        return True

    def __iter__(self):
        its = [{
            # null leg, for binding front leg
            "id": 0,
            "current": { "m": 0, "y": 0 }, 
            "range": None,
            "init": None
        }]
        legs = self.get_legs()

        for leg in legs:
            its.append({
                "current": { "m": None, "y": None },
                "range": { "m": [ None, None ], "y": [ None, None ] },
                "init": { "m": [ leg[0], leg[1] ], "y": [ leg[2], leg[3] ] },
            })

        # initialize range and current values
        for i in range(1, len(its)):
            if not self.init_it(its[i], its[i - 1]): 
                return [ "INVALID SPECIFCATION" ]

        self.set_its(its)

        return self

    def __next__(self):
        its = self.get_its()
        i = len(its) - 1
        j = i

        to_inc = i
        to_init = None
        refresh = False

        # account for first iteration
        legs = [ (it["current"]["m"], it["current"]["y"]) for it in its[1:] ]

        while (True):
            if to_inc:
                success = self.increment_it(its[to_inc])
                if success:
                    to_init = to_inc + 1
                    to_inc = None
                else:
                    to_inc -= 1
                    if to_inc == 0:
                        # outer loop finished
                        raise StopIteration
            elif to_init:
                if to_init > j:
                    # loop N incremented, N+1-M successfully initialized
                    break
                else:
                    success = self.init_it(its[to_init], its[to_init - 1])
                    if (success):
                        to_init += 1
                    else:
                        # initialized into bad range, try incrementing previous 
                        # loop; refresh output to get rid of bad range
                        refresh = True
                        to_inc = to_init - 1

        if refresh:
            legs = [ (it["current"]["m"], it["current"]["y"]) for it in its[1:] ]

        return legs

if __name__=="__main__":
    legs = [
        [ "Q", "Z", "0", "1", "A" ],
        [ "+1", "Z", "+0", "+1", "B" ]
    ]

    it = contract_iterator(legs)

    for match in it:
        print(match)