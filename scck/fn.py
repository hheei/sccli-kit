import sys

class Prompt:
    def __init__(self, cmd_lst: list = []):
        self.last_cmd = None
        self.cmd_lst = cmd_lst
        
    def __call__(self, s: str):
        print(s, end="")
        if len(self.cmd_lst) > 0:
            ans = self.cmd_lst.pop(0)
            print(ans)
        else:
            inp = input().strip()
            if inp != "":
                self.cmd_lst.extend(inp.split())
                ans = self.cmd_lst.pop(0)
            else:
                ans = ""
        
        self.last_cmd = self.proc_cmd(ans)
        
        return self.last_cmd
        
    def proc_cmd(self, cmd: str):
        if cmd.isdigit() and cmd != "0":
            return cmd.strip().lstrip("0")
        else:
            return cmd.strip()

prompt = Prompt(sys.argv[1:])

def is_option_yes(s: str):
    return s.strip().lower() in ["y","yes","1","t", "true"]

def get_str_width(s: str):
    return int((len(s.encode('utf-8')) - len(s))/2 + len(s))