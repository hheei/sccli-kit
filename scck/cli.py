import sys
from scck.basic import run_genjob
from scck.info import run_gen_user_info, run_slurm_table_generator, run_dirstat
from scck.const import title, cmdlen
from scck.fn import prompt


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
    
    if len(sys.argv) > 1 and sys.argv[1] == "cfg":
        # scck cfg Users.$USER.short.0
        from scck.info import CFG
        args = sys.argv[2].split(".")
        value = CFG
        try:
            for arg in args:
                if arg.isdigit():
                    value = value[int(arg)]
                else:
                    value = value[arg]
                    
            print(value, end="")
            exit(0)
        except KeyError as e:
            print(sys.argv[2])
            raise e
        
    else:
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
            