# prints lines of unicode gibberish to a file
import random

outfp = "gibberish.txt"

N = 50

LINELEN = 80

UNI = 255


rnd = [chr(i) for i in range(UNI) if chr(i).isprintable()]

with open(outfp, "w", encoding="utf-8") as out:
    for i in range(0, N):
        a = repr("".join(random.sample(rnd, LINELEN)))
        print(a, file=out)
