import os
import json
from ..const import config_path
from .auto import update_user_info

_name = os.getenv('USER') or os.getenv('LOGNAME')

if not config_path.exists():
    CFG = update_user_info()
else:
    CFG = json.loads(config_path.read_text())

if _name is not None and _name not in CFG["Users"]:
    CFG = update_user_info()