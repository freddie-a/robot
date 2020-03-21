import sys
import select
a = 0

def out(a):
    print(a, "seconds")

def main(a):
    a += 1
    print(a)
    i, o, e = select.select([sys.stdin], [], [], 0.1)
    if (i):
        out(a)
    else:
        main(a)
main(a)