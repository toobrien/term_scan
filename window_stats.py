from numpy import std, cov as npcov
from numpy.random import randn
from statistics import stdev
from math import sqrt, pow
from matplotlib import pyplot as plt


class var:
# https://stackoverflow.com/questions/14635735/how-to-efficiently-calculate-a-moving-standard-deviation

    def __init__(self, win_len):
        self.win_len = win_len
        self.var_0 = 0
        self.var_1 = 0
        self.avg_0 = 0
        self.avg_1 = 0
        self.sum = 0
        self.sum_sq = 0


    def clear(self):
        self.__init__(win_len)


    # not working at all
    def next_stable(self, x, i):
        x_i = x[i]

        if i == 0:
            n = 1
            self.avg_1 = x_i
            self.var_1 = 0
        elif i < self.win_len:
            # this works
            n = i + 1
            self.avg_1 = self.avg_0 + (x_i - self.avg_0) / n
            self.var_1 = self.var_0 + (x_i - self.avg_0) * (x_i - self.avg_1)
        else:
            # this does not
            n = self.win_len
            x_0 = x[i - n]
            self.avg_1 = self.avg_0 + (x_i - x_0) / n
            self.var_1 =    self.var_0 + \
                            (x_i - self.avg_1 + x_0 - self.avg_0) * \
                            (x_i - x_0) / (n - 1)
        
        self.avg_0 = self.avg_1
        self.var_0 = self.var_1

        return self.var_1 / (n - 1) if n > 1 else self.var_1

    # subject to "instability"
    def next(self, x, i):
        x_i = x[i]

        n = min(i + 1, self.win_len)

        if n == self.win_len:
            x_0 = x[i - n]

            self.sum -= x_0
            self.sum_sq -= pow(x_0, 2)
        
        self.sum += x_i
        self.sum_sq += pow(x_i, 2)

        if n > 1:
            var = (self.sum_sq - pow(self.sum, 2) / n) / n
        else:
            var = 0

        return var


class avg:


    def __init__(self, win_len):
        self.win_len = win_len
        self.sum = 0


    def clear(self):
        self.__init__(self.win_len)


    def next(self, x, i):
        x_i = x[i]
        
        n = min(i + 1, self.win_len)

        if n == self.win_len:
            x_0 = x[i - self.win_len]
            self.sum -= x_0
        
        self.sum += x_i

        return self.sum / n


class cov:
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Covariance

    def __init__(self, win_len):
        self.win_len = win_len
        self.x = 0
        self.y = 0
        self.xy = 0


    def clear(self):
        self.__init__(self.win_len)


    def next(self, x, y, i):
        x_i = x[i]
        y_i = y[i]

        n = min(i + 1, self.win_len)

        if n == self.win_len:
            x_0 = x[i - n]
            y_0 = y[i - n]

            self.x -= x_0
            self.y -= y_0
            self.xy -= x_0 * y_0
        
        self.x += x_i
        self.y += y_i
        self.xy += x_i * y_i

        return (self.xy - (self.x * self.y) / n) / n


if __name__ == "__main__":
    mode = "cov"
    win_len = 30

    if mode == "var":
        n = 1000
        sigma = 5
        x = [ sigma * randn() for i in range(n) ]
        x_ = range(win_len, n)

        wv = var(win_len)

        t0 = [ sqrt(wv.next_(x, i)) for i in range(len(x)) ]
        t1 = [ sqrt(wv.next(x, i)) for i in range(len(x)) ]
        t2 = [ stdev(x[max(0, i - win_len):i]) for i in range(2, len(x)) ]
        t3 = [ std(x[max(0, i - win_len):i]) for i in range(2, len(x)) ]

        for t in [ t2, t3 ]:
            t.insert(0,0)
            t.insert(0,0)

        for i in range(len(x) - 2):
            print(t0[i], t1[i], t2[i], t3[i])
            if (i == win_len - 1):
                print("\n")
        
        fig, axs = plt.subplots(2, 2)
        axs[0, 0].plot(x_, t0[win_len:])
        axs[0, 1].plot(x_, t1[win_len:])
        axs[1, 0].plot(x_, t2[win_len:])
        axs[1, 1].plot(x_, t3[win_len:])
        plt.show()
    elif mode == "cov":
        n = 1000
        x_ = range(win_len, n)
        x = [ randn() for i in range(n) ]
        y = [ randn() for i in range(n) ]

        wc = cov(win_len)
        t0 = [ wc.next(x, y, i) for i in range(n) ]
        t1 = [ 
                npcov(
                    [
                        x[max(0, i - win_len):i],
                        y[max(0, i - win_len):i]
                    ]
                )[0, 1]
                for i in range(2, n)
            ]

        t1.insert(0,0)
        t1.insert(0,0)

        fix, (ax0, ax1) = plt.subplots(2)
        
        ax0.plot(x_, t0[win_len:])
        ax1.plot(x_, t0[win_len:])
        
        plt.show()