import os
import sys


class ConstantManager:
    config_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), 'config.ini')