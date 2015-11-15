#!/usr/bin/python

# PyChess startup script.
# This script is to check package requirements, and set up system/enviroment
# stuff, to make the PyChess Main class run smoothly.

from __future__ import print_function
import argparse
import os, sys

# faulthandler will be in Python 3.3; for 2.x you can download it from pypi
if not getattr(sys, 'frozen', False):
    try:
        import faulthandler
        faulthandler.enable()
    except ImportError:
        pass

###############################################################################
# Check requirements

if sys.version_info < (2, 7, 0):
    print('ERROR: PyChess requires Python >= 2.7')
    sys.exit(1)

try:
    import cairo
except ImportError as e:
    print("ERROR: Not all dependencies installed! You can find them in INSTALL")
    print(e)
    sys.exit(1)
