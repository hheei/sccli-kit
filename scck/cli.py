import sys
from .basic import run_genjob
from .const import title, cmdlen
from .fn import prompt


callbacks = {
    "Basic": [
        ("1", "Print Hello World", lambda: print("Hello, World!") or True),
        ("2", "Generate jobs script on cluster", lambda: run_genjob() or True),
    ]
}

def run():
    def print_title():
        print(" ", end="")
        # Print all available options
        print(title)
        
        for c, cbs in callbacks.items():
            print(" ", end="")
            print(f" {c} ".center(cmdlen, "="))
            for cb in cbs:
                calls[cb[0]] = cb[2]
                cmd_str = f"{cb[0].rjust(2, '0') if cb[0].isdigit() else cb[0]})"
                print(f" {cmd_str.ljust(3)} {cb[1]}")
        
        return print("\n q)  Exit")
    
    calls: dict = {"q": lambda: sys.exit(0)}
    print_title()
    
    # Main loop
    while True:
        cmd = prompt(" ----->\n")
        
        if cmd in calls:
            if not calls[cmd]():
                calls["q"]()
            else:
                print_title()
        else:
            raise ValueError(f"Command `{cmd}` not found")