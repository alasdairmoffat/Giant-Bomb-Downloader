import sys
import os


def exit_process():
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)