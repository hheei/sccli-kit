import re
import subprocess
import os
from pathlib import Path
from collections import defaultdict
import sys

from ..const import cmdlen
from ..fn import get_str_width
from ..info import CFG

def is_relative_to(child, parent):
    child = os.path.realpath(child)
    parent = os.path.realpath(parent)
    return os.path.commonpath([child, parent]) == parent

def run_slurm_table_generator():
    try:
        result = subprocess.run(
            ["squeue", "-u", os.getenv('USER') or os.getenv('LOGNAME') or '', "-o", "%i,%P,%j,%t,%M,%D", "--noheader"],
            capture_output=True, text=True, check=True
        ).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(" No SLURM is found.")
        sys.exit(0)
    
    # [[job_id, partition, job_name, state, time, nodes]]
    if result:
        jobs = list(map(lambda x: x.split(","), result.split('\n')))
    else:
        jobs = []
    
    JOBS_CATEGORIES = defaultdict(lambda: list())
    
    SHORT_TO_USER = {short: user for user, values in CFG['Users'].items() for short in values['short']}
    ROOT_TO_USER = {Path(values['root']): user for user, values in CFG['Users'].items()}
    
    for job in jobs:
        job_prefix = job[2].replace("_", "-").split("-")[0]
        if job_prefix in SHORT_TO_USER:
            JOBS_CATEGORIES[SHORT_TO_USER[job_prefix]].append(job)
        else:
            try:
                sc_result = subprocess.run(
                    ["scontrol", "show", "job", job[0]],
                    capture_output=True, text=True, check=True
                )
            except subprocess.CalledProcessError:
                JOBS_CATEGORIES['Other'].append(job)
            else:
                match = re.search(r'Command=([^\s]+)', sc_result.stdout)
                if match:
                    command_path = Path(match.group(1))
                    for root, user in ROOT_TO_USER.items():
                        if is_relative_to(str(command_path), str(root)):
                            JOBS_CATEGORIES[user].append(job)
                            break
                    else:
                        JOBS_CATEGORIES['Other'].append(job)
                else:
                    JOBS_CATEGORIES['Other'].append(job)
    
    num_jobs = len(jobs)
    node_running = sum(map(lambda x: int(x[5]), filter(lambda x: x[3] == "R", jobs)))
    node_pending = sum(map(lambda x: int(x[5]), filter(lambda x: x[3] == "PD", jobs)))
    node_configu = sum(map(lambda x: int(x[5]), filter(lambda x: x[3] == "CF", jobs)))
    
    user_stats = defaultdict(lambda: {'PD': 0, 'R': 0, 'CF': 0})
    
    for user, jobs in JOBS_CATEGORIES.items():
        user_stats[user]['PD'] = len(list(filter(lambda x: x[3] == "PD", jobs)))
        user_stats[user]['R'] = len(list(filter(lambda x: x[3] == "R", jobs)))
        user_stats[user]['CF'] = len(list(filter(lambda x: x[3] == "CF", jobs)))
    
    print(" " + " SLURM JOBS ".center(cmdlen, "="))
    print(f" Jobs: {num_jobs} \n")
    MAX_USER_WIDTH = max(list(map(lambda x: get_str_width(CFG['Users'][x]['name']), CFG['Users'].keys())) + [0])
    ELENAME_WIDTH = max(10, (cmdlen - MAX_USER_WIDTH - 2) // 3)
    print(" " + f"{'User'.center(MAX_USER_WIDTH + 2)}{'Pending'.center(ELENAME_WIDTH)}{'Running'.center(ELENAME_WIDTH)}{'Configuring'.center(ELENAME_WIDTH)}")
    print(" " + "-" * cmdlen)
    for user in sorted(CFG['Users'].keys(), key=lambda x: user_stats[x]['R'], reverse=True):
        stats = user_stats[user]
        user_show_name = CFG['Users'][user]['name']
        fmt_width = MAX_USER_WIDTH - get_str_width(user_show_name) + len(user_show_name) + 2
        print(f" {user_show_name.ljust(fmt_width)}{str(stats['PD']).center(ELENAME_WIDTH)}{str(stats['R']).center(ELENAME_WIDTH)}{str(stats['CF']).center(ELENAME_WIDTH)}")
        
    if 'Other' in user_stats:
        print(" " + "-" * cmdlen)
        print(" " + f"Other".ljust(MAX_USER_WIDTH + 2) + str(user_stats['Other']['PD']).center(ELENAME_WIDTH) + str(user_stats['Other']['R']).center(ELENAME_WIDTH) + str(user_stats['Other']['CF']).center(ELENAME_WIDTH))
    
    print(" " + "-" * cmdlen)
    print(" " + f"Total".ljust(MAX_USER_WIDTH + 2) + str(node_pending).center(ELENAME_WIDTH) + str(node_running).center(ELENAME_WIDTH) + str(node_configu).center(ELENAME_WIDTH))

    sys.exit(0)

