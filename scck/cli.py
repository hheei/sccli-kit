import sys
from .basic import run_genjob
from .info import run_gen_user_info, run_slurm_table_generator, run_dirstat
from .const import title, cmdlen
from .fn import prompt


callbacks = {
    "Basic": [
        ("1", "Print Hello World", lambda: print("Hello, World!") or True),
        ("2", "Generate jobs script on cluster", lambda: run_genjob() or True),
    ],
    "Info": [
        ("90", "User Information", lambda: run_gen_user_info() or True),
        ("91", "Slurm jobs statistics", lambda: run_slurm_table_generator() or True),
        ("92", "Directory statistics", lambda: run_dirstat() or True),
    ]
}

def run():
    args = sys.argv[1:]
    
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
        if args:
            print("")
            cmd = args.pop(0)
        else:
            cmd = prompt(" ----->\n")
        
        if cmd in calls:
            if not calls[cmd]():
                calls["q"]()
            else:
                print_title()
        else:
            raise ValueError(f"Command `{cmd}` not found")