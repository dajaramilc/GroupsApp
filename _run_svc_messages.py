import importlib.util, sys, os
spec = importlib.util.spec_from_file_location("main", os.path.join(os.path.dirname(__file__), "services", "svc-messages", "main.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
app = mod.app
