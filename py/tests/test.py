import math

earthRadius = 6371000  # meters
equatorRadius = 6378137
poleRadius = 6356752
maxCurveRadius = (equatorRadius**2)/poleRadius


def sssAngle(R1, R2, l):
    cosv = ((R1**2 + R2**2 - l**2)/(2*R1*R2))
    return(math.acos(cosv) if cosv <= 1 else math.acos(cosv**-1))

def sssAngle2(R1, R2, l):
    return(+R1**2+R2**2-2*R1*R2-l**2)

print(sssAngle(poleRadius, earthRadius, 25))