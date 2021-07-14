# GE and CL have the most listed contracts, at 120
TERMS_DOMAIN = [0, 119]

class terms_iterator:
    # this class is almost entirely copied from 
    # contract_iterator... should probably combine them
    
    def __init__(self, legs):
        self.set_legs(legs)


    def set_legs(self, legs): self.legs = legs
    def get_legs(self): return self.legs
    def set_its(self, its): self.its = its
    def get_its(self): return self.its
    def set_finished(self, finished): self.finished = finished
    def get_finished(self): return self.finished


    def __next__(self):
        if self.get_finished(): raise StopIteration

        its = self.get_its()
        i = len(its) - 1
        j = i

        to_inc = i
        to_init = None

        # properly set from previous iteration or init
        legs = [ 
            (it["current"]["term"], it["current"]["side"])
            for it in its[1:] 
        ]

        while (True):
            if to_inc:
                if(self.increment_it(its[to_inc])):
                    to_init = to_inc + 1
                    to_inc = None
                else:
                    to_inc -= 1
                    if to_inc == 0:
                        # outer loop finished, but latest result valid
                        self.set_finished(True)
                        break
            elif to_init:
                if to_init > j:
                    # loop N incremented, N+1-M successfully initialized
                    break
                else:
                    if(self.init_it(its[to_init], its[to_init - 1])):
                        to_init += 1
                    else:
                        # loop initialized into bad range;
                        # try incrementing previous loop
                        to_inc = to_init - 1

        return tuple(legs)


    def __iter__(self):
        self.set_finished(False)

        its = [{
            # null leg, for binding front leg
            "current": { "term": 0 },
            "range": None,
            "init": None
        }]

        legs = self.get_legs()

        for leg in legs:
            its.append({
                "current": { "term": leg[0], "side": leg[2] }, 
                "range": [ None, None ],
                "init": [ leg[0], leg[1] ]
            })

        # initialize range and current values
        for i in range(1, len(its)):
            if not self.init_it(its[i], its[i - 1]): 
                return [ "INVALID SPECIFCATION" ]

        self.set_its(its)

        return self


    def increment_it(self, it):        
        cur = it["current"]
        rng = it["range"]

        if cur["term"] < rng[1]:
            cur["term"] += 1
        else:
            return False

        return True


        # - binds the current iterator's range using the previous
        #   iterator's current value, if necessary
        # - sets the current iterator's value
    def init_it(self, cur, prev):
            cur_val = cur["current"]
            cur_rng = cur["range"]
            cur_ini = cur["init"]
            prev_term = prev["current"]["term"]
            
            # bind range
            for i in (0,1):
                if "+" in cur_ini[i]:
                    cur_rng[i] = prev_term + int(cur_ini[i][1:])
                else:
                    cur_rng[i] = int(cur_ini[i])
                
            # initialize current index
            cur_val["term"] = cur_rng[0]

            # validate range and domain
            return  cur_rng[0] >= TERMS_DOMAIN[0] and \
                    cur_rng[1] <= TERMS_DOMAIN[1]
    

if __name__=="__main__":
    examples = {
        "one_width_butterfly": [
            [ "0", "10", "A" ],
            [ "+1", "+1", "B" ],
            [ "+0", "+0", "B" ],
            [ "+1", "+1", "A" ]
        ],
        "6_month_calendar": [
            [ "0", "119", "A" ],
            [ "+1", "+6", "B" ]
        ]
    } 

    its = [
        terms_iterator(examples["one_width_butterfly"]),
        terms_iterator(examples["6_month_calendar"])
    ]

    for it in its:
        for match in it:
            print(match)