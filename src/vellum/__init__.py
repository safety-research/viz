"""viz's old name. `import vellum` and `from vellum.gallery import ...` keep working; new code should `import viz`."""
import importlib
import pkgutil
import sys

import viz

for _m in pkgutil.walk_packages(viz.__path__, "viz."):
    sys.modules.setdefault("vellum" + _m.name[len("viz"):], importlib.import_module(_m.name))
sys.modules[__name__] = viz
