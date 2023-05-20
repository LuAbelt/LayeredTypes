import importlib.util
import sys

from layers.Layer import Layer
from pathlib import Path

class LayerImplWrapper:
    def __init__(self,
                 layer_base_dir,
                 layer: Layer):
        self.layer = layer
        self.layer_base_dir = Path(layer_base_dir)

        if not self.layer_base_dir.is_dir():
            raise FileNotFoundError(f"Could not find layer base directory at {self.layer_base_dir}")

        full_path = Path(self.layer_base_dir, f"{layer.name}.py")

        if not full_path.is_file():
            raise FileNotFoundError(f"No implementation file (tried to load file '{full_path}') found for layer '{layer.name}'")

        module_name = f"layers.{self.layer.name}"
        spec = importlib.util.spec_from_file_location(module_name, full_path)
        self.module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = self.module
        spec.loader.exec_module(self.module)

        self.depends_on = getattr(self.module, "depends_on", lambda : set())
        self.typecheck = getattr(self.module, "typecheck")
        self.parse_type = getattr(self.module, "parse_type", lambda x: x)
        self.run_before = getattr(self.module, "run_before", lambda : set())
