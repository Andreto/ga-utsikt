# Copyright (c) 2022 Andreas Törnkvist | MIT License

import math

class worldfile:
    def __init__(self, filename):
        wFile = open(filename)
        w = wFile.readlines()
        w = [line.rstrip() for line in w]

        self.A = float(w[0])
        self.D = float(w[1])
        self.B = float(w[2])
        self.E = float(w[3])
        self.C = float(w[4])
        self.F = float(w[5])

        Xv = math.atan(self.D/self.A)
        Yv = math.atan(self.B/self.E)

        self.Xx = (math.cos(Xv) ** 2) / self.A
        self.Xy = (math.cos(Xv) * math.sin(Xv)) / self.A
        self.Yy = (math.cos(Yv) ** 2) / self.E
        self.Yx = (math.cos(Yv) * math.sin(Yv)) / self.E
        
    def coordToPx(self, lon, lat):
        Dx = lon - self.C
        Dy = lat - self.F

        Px = (Dx * self.Xx) + (Dy * self.Yx)
        Py = (Dx * self.Xy) + (Dy * self.Yy)

        return(Px, Py)

        
