# conftest.py  ← 放在项目根目录，和 tools.py 同级
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))