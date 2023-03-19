import os
import sys

adspPath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if not adspPath in sys.path:
    sys.path.insert(0, adspPath)

import adsp
