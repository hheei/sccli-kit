from scck.const import title, cmdlen

def run_main(args):
    import sys
    from scck.fn import Prompt
    from scck.error import BackException
    from scck.basic import run_genjob
    from scck.info import run_gen_user_info, run_slurm_table_generator, run_dirstat
    callbacks = {
        "Basic": [
            (1, "Print Hello World", lambda p: print("Hello, World!")),
            (2, "Generate jobs script on cluster", run_genjob),
        ],
        "Info": [
            (11, "Slurm jobs statistics", run_slurm_table_generator),
            (12, "Directory statistics", run_dirstat),
        ],
        "Debug": [
            (90, "Auto configuration", run_gen_user_info),
        ]
    }

    calls = {v[0]: v[2] for vs in callbacks.values() for v in vs}
    calls.update({"q": lambda p: sys.exit(0)})
    
    def get_title():
        global title
        lines = [f" {title}"]
        for c, cbs in callbacks.items():
            lines.append(f" {(' ' + c + ' ').center(cmdlen, "=")}")
            for cb in cbs:
                if isinstance(cb[0], int):
                    call_id = f"{cb[0]:02d}"
                elif cb[0].isdigit():
                    call_id = cb[0].rjust(2, "0")
                else:
                    call_id = cb[0]
                lines.append(f" {call_id}) {cb[1]}")
        lines.append("")
        lines.append(" q) Exit")
        return "\n".join(lines)
    
    args = dict(vars(args))
    p = Prompt(args['exec'], silent = args['silent'])
    title = get_title()
    while True:
        if not args['silent']:
            print(title)
        cmd = p.ask()
        
        if cmd.isdigit():
            cmd = int(cmd)
            
        if cmd in calls:
            try:
                r = calls[cmd](p)
                sys.exit(r)
                    
            except BackException:
                continue
            except Exception as e:
                raise e
                
        else:
            raise ValueError(f"Command `{cmd}` not found")

def run_cfg(args):
    from scck.info import CFG
    args = args.name.split(".")
    value = CFG
    try:
        for arg in args:
            if arg.isdigit():
                value = value[int(arg)]
            else:
                value = value[arg]
        print(value, end="")
        
    except KeyError as e:
        print("", end="")
        
    exit(0)
    
def run_job_init(args):
    import os
    from datetime import datetime
    from pathlib import Path
    from scck.fn import get_user_name
    from scck.info import CFG
    date = datetime.now().strftime("%Y%m%d")
    name = get_user_name()
    job_submit_dir = Path(os.getenv('SLURM_SUBMIT_DIR', "UNK-DIR")).expanduser()
    job_id = os.getenv('SLURM_JOB_ID', "UNK-ID")
    if not (job_submit_dir / f"slurm-{job_id}.out").exists():
        return
    
    job_log_dir = Path(CFG['Config']['job_log_dir']).expanduser() / name
    job_log_dir.mkdir(parents=True, exist_ok=True)
    
    save_name = f"{date}-{job_id}"
    
    if (job_submit_dir / f"slurm.out").exists():
        (job_submit_dir / f"slurm.out").unlink()
    if (job_submit_dir / f"slurm.err").exists():
        (job_submit_dir / f"slurm.err").unlink()
    if (job_log_dir / f"{save_name}.{job_id}.out").exists():
        (job_log_dir / f"{save_name}.{job_id}.out").unlink()
    if (job_log_dir / f"{save_name}.{job_id}.err").exists():
        (job_log_dir / f"{save_name}.{job_id}.err").unlink()
        
    Path(job_submit_dir / f"slurm.out").symlink_to(job_submit_dir / f"slurm-{job_id}.out")
    Path(job_submit_dir / f"slurm.err").symlink_to(job_submit_dir / f"slurm-{job_id}.err")
    Path(job_log_dir / f"{save_name}.{job_id}.out").symlink_to(job_submit_dir / f"slurm-{job_id}.out")
    Path(job_log_dir / f"{save_name}.{job_id}.err").symlink_to(job_submit_dir / f"slurm-{job_id}.err")

def run_job_user(args):
    from scck.fn import get_user_name
    from scck.info import CFG
    name = get_user_name()
    print(CFG['Users'][name]['short'][0], end="")

def run():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.set_defaults(func=run_main)
    parser.add_argument("-x", "--exec", 
                        help="Execute the command split by ' ' and default option is '@'.", 
                        default=None, 
                        type=str)
    parser.add_argument("-s", "--silent", action="store_true", help="Silent mode.", default=False)
    subparsers = parser.add_subparsers()
    p_cfg = subparsers.add_parser("cfg", help="Get config value from .sccli-kit.")
    p_cfg.add_argument("name", help="Name of the config value", type=str)
    p_cfg.set_defaults(func=run_cfg)
    
    p_job = subparsers.add_parser("job", help="Automatic script for job.")
    job_parsers = p_job.add_subparsers()
    p_job_init = job_parsers.add_parser("init", help="Initialize job enviroment.")
    p_job_init.set_defaults(func=run_job_init)
    p_job_user = job_parsers.add_parser("user", help="Detect user information.")
    p_job_user.set_defaults(func=run_job_user)
    
    # p_refresh = subparsers.add_parser("refresh", help="Refresh module information.")
    # p_refresh.set_defaults(func=run_refresh)
    
    args = parser.parse_args()
    args.func(args)
    
if __name__ == "__main__":
    run()