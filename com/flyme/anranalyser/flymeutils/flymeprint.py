import sys


def errorprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
