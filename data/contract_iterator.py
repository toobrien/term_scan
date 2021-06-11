from data.months import months
from json import dumps

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
    YEAR_DOMAIN = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
    SIDE_DOMAIN = ('A', 'B')

    def __init__(self, legs):
        self.set_legs(legs)

    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs

    def set_its(self, its): self.its = its
    def get_its(self): return self.its

    def init_leg_it(self, cur, prev):
        # sets cur's range and current values by 
        # binding the initializer values. e.g.:
        # 
        # prev current month:           1
        # cur month initializer:        ("+2", "V")
        #
        # results in:
        #
        # cur current month:            3
        # cur range:                    (3, 9)
        m_r = cur["range"]["m"]
        m_i = cur["init"]["m"]
        y_r = cur["range"]["y"] 
        y_i = cur["init"]["y"]

        # bind range
        for i in (0,1):
            if "+" in m_i[i]:
                m_r[i] = prev["current"]["m"][0] + int(m_i[i][1:])
            else:
                m_r[i] = self.MONTH_DOMAIN[m_i[i]]
            if "+" in y_i[i]:
                y_r[i] = prev["current"]["y"][0] + int(y_i[i][1:])
            else:
                y_r[i] = int(y_i[i])
            
        # initialize current
        cur["current"]["m"] = cur["range"]["m"][0]
        cur["current"]["y"] = cur["range"]["y"][0] 


    def __iter__(self):
        its = [{
            # null leg, for binding leg 1
            "current": { "m": 0, "y": 0 }, 
            "range": None,
            "init": None
        }]
        legs = self.get_legs()

        for leg in legs:
            its.append({
                "current": { "m": None, "y": None },
                "range": { "m": (None, None), "y": (None, None) },
                "init": { "m": (leg[0], leg[1]), "y": (leg[2], leg[3]) },
            })

        # initialize range and current values
        for i in range(1, len(its)):
            self.init_leg_it(its[i], its[i - 1])

        self.set_its(its)

    def __next__(self):
        its = self.get_its()
        i = len(its) - 1
        j = i

        while (i > 0):
            it = its[-i]
            cur = it["current"]
            rng = it["range"]
            if cur["m"] < rng["m"][1]:
                cur["m"] = cur["m"] + 1
                break
            elif cur["y"] < rng["y"][1]:
                cur["y"] = cur["y"] + 1
                cur["m"] = rng["m"][0]
                break
            else:
                # end of this leg's loop, start on previous leg
                # re-initialize this one below
                i -= 1

        if i == 0:
            # front leg finished iterating, all done
            raise StopIteration
        else:
            # some legs need to be re-initialized
            while (i < j):
                i += 1
                self.init_leg_it(its[i], its[i - 1])

        return [ (it["current"]["m"], it["current"]["y"]) for it in its[1:] ]


if __name__=="__main__":
    legs = [
        [ "Q", "Z", "0", "1", "A" ],
        [ "+1", "Z", "0", "1", "B" ]
    ]

    it = contract_iterator(legs)

    for match in it:
        print(match)