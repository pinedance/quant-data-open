import yaml
from pathlib import Path
import threading

class ConfigManager:
    _instance = None
    _lock = threading.Lock()
    _config = {}

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._load_config()
            return cls._instance

    def _load_config(self):
        # Resolve config.yaml in the project root (grandparent of core/config.py)
        base_dir = Path(__file__).resolve().parent.parent
        config_path = base_dir / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"⚠️  Error loading config.yaml from {config_path}: {e}")
        else:
            print(f"⚠️  config.yaml not found at {config_path}")

    def get_constants(self) -> dict:
        return self._config.get("constants", {})

    def get_pages(self) -> list:
        return self._config.get("pages", [])

    def get_paths(self) -> dict:
        return self._config.get("paths", {})
