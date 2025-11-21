import sys
import os
from io import StringIO
from datetime import datetime
from pathlib import Path
from typing import Any

from scck.error import BackException

class Prompt:
    def __init__(self, inp = None, prompt = " ----->", default_str = "@", silent = False):
        self.history = []
        self.future = []
        if inp is not None:
            self.future.extend(inp.strip().split())
        self.prompt = prompt
        self.ds = default_str
        self.out = StringIO() if silent else sys.stdout

    def ask(self, inp = None):
        if self.future:
            ans = self.future.pop(0)
            if ans == self.ds or ans == "":
                ans = self.ds
            print(ans, file=self.out)
        else:
            if inp is None:
                inp = input().strip()
                if inp == "":
                    inp = self.ds
                    
            self.future.extend(inp.strip().split())
            ans = self.future.pop(0)
                
        self.history.append(ans)
        return ans

    def fill(self, title: str, default: str = None, mapper: callable = None, checker: callable = None):
        print(title, file=self.out)
        ans = self.ask()
        if ans == self.ds:
            ans = default
            
        if mapper is not None:
            ans = mapper(ans)
        if checker is not None and not checker(ans):
            raise ValueError(f"Invalid input: {ans}!")
        return ans

    def select(self,
               title: str, 
               options: list[str] | dict[Any, str], 
               append_back = True, 
               append_exit = True, 
               default_option = None, 
               left_str = " ", 
               right_str = ") "
               ):
        print(title, file=self.out)
        if isinstance(options, dict):
            max_digit = max(options.keys(), lambda x: len(str(x)))
            assert "b" not in options and "q" not in options, "b and q are reserved keywords!"
            for i, option in options.items():
                print(f"{left_str}{i:>{max_digit}s}{right_str}{option}", file=self.out)
        else:
            max_digit = len(str(len(options) - 1))
            for i, option in enumerate(options):
                print(f"{left_str}{i:0{max_digit}d}{right_str}{option}", file=self.out)
        print(file=self.out)
        if append_back:
            print(f"{left_str}b{right_str} Back", file=self.out)
        if append_exit:
            print(f"{left_str}q{right_str} Exit", file=self.out)
        print(self.prompt, file=self.out)
        ans = self.ask()
        if ans == "b":
            raise BackException
        elif ans == "q":
            sys.exit(0)
        elif default_option is not None and ans == self.ds:
            return default_option
        elif isinstance(options, dict) and ans in options:
            return ans
        elif isinstance(options, list) and ans.isdigit() and 0 <= int(ans) < len(options):
            return int(ans)
        else:
            raise ValueError(f"Invalid selection: {ans}!")
        
def parse_time(s: str):
    formats = [
        "%H",           # 时
        "%d-%H",        # 日-时
        "%H:%M",        # 时:分
        "%d-%H:%M",     # 日-时:分
        "%H:%M:%S",     # 时:分:秒
        "%d-%H:%M:%S",  # 日-时:分:秒
    ]

    for fmt in formats:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass

    raise ValueError(f"Cannot parse time format: {s}")

def get_user_name():
    from scck.config import CFG
    for name, value in CFG["Users"].items():
        try:
            Path.cwd().relative_to(Path(value["root"]).expanduser())
            return name
        except ValueError:
            continue
    return os.getenv('USER', "UNK")

def is_option_yes(s: str):
    return s.strip().lower() in ["y","yes","1","t", "true"]

def get_str_width(s: str):
    return int((len(s.encode('utf-8')) - len(s))/2 + len(s))

def get_python_venv():
    conda_exe_path = os.environ.get("CONDA_EXE", None)
    out = {
        "conda": [],
        "venv": []
    }
    if conda_exe_path is not None:
        conda_env_path = Path(conda_exe_path).parent.parent / "envs"
        for env_path in conda_env_path.iterdir():
            if env_path.is_dir():
                out["conda"].append(env_path.name)
        
        if Path("~/.conda/envs").expanduser().exists():
            for env_path in Path("~/.conda/envs").expanduser().iterdir():
                if env_path.is_dir():
                    out["conda"].append(env_path.name)
        out["conda"].sort()
    
    for path in Path().glob("*"):
        if path.is_dir() and (path / "bin/activate").exists():
            out["venv"].append(path.name)
    out["venv"].sort()
    
    return out