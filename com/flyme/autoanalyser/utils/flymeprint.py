import sys
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    stream=sys.stdout)


# def warning(*args, **kwargs):
#    print(*args, file=sys.stderr, flush=True, **kwargs)

def error(message):
    logging.error(message)


def warning(message):
    logging.warning(message)


def debug(message):
    logging.debug(message)
