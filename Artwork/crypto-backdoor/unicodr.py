# prints lines of unicode gibberish to a file

outfp = "gibberish.txt"

N = 50

LINELEN = 80

import random
import math

UNI = 255


rnd = [chr(l) for l in range(UNI) if chr(l).isprintable()]

with open(outfp, "w", encoding='utf-8') as out:
    for i in range(0, N):
        a = repr("".join(random.sample(rnd, LINELEN)))
        print(a, file=out)


    
