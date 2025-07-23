"""This script helps pytest to properly import modules in scripts located in src"""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
print(sys.path)
