import sys
from pathlib import Path
from difflib import get_close_matches

from scck.const import cmdlen
from scck.fn import Prompt, parse_time, get_user_name
from scck.config import CFG
from scck.basic.jobgen_template import run_options

def run_genjob(p: Prompt, *args, **kwargs):
    print(f" {' Job Generator '.center(cmdlen, '=')}")

    users = list(CFG["Users"].keys())
    if len(users) == 1:
        user = users[0]
    else:
        try:
            user = users[users.index(get_user_name())]
        except IndexError:    
            user = users[p.select(
                title = " Select the user:",
                options = users,
                default_option = 0,
            )]
        
    partitions = list(CFG["Cluster"].keys())
    if len(partitions) == 1:
        partition = partitions[0]
    else:
        partition = partitions[p.select(
            title = " Select the partition:",
            options = partitions,
            default_option = 0,
        )]
    
    # Quality of service
    qoss = CFG["Cluster"][partition]["QOS"]
    
    if len(qoss) == 0:
        qos = None
    elif len(qoss) == 1:
        qos = qoss[0]
    else:
        default_option = get_close_matches("normal", qoss, n=1)
        if default_option == []:
            default_option = 0
        else:
            default_option = qoss.index(default_option[0])
        qos = qoss[p.select(
            title = " Select the quality of service:",
            options = qoss,
            default_option = default_option,
        )]

    # Time
    timelimit = CFG["Cluster"][partition]["TIMELIMIT"]
    timelimit = p.fill(
        title = f" Task running time (d-HH:MM:SS, default: {parse_time(timelimit).strftime('%d-%H:%M:%S')})",
        default = timelimit,
        mapper  = parse_time,
        checker = lambda x: x <= parse_time(timelimit),
    )
    
    node = CFG['Cluster'][partition]['NODES']
    node = p.fill(
        title = f" Number of nodes: (1≤x≤{node})",
        default = 1,
        mapper  = int,
        checker = lambda x: 1 <= x <= node,
    )
    
    max_gpu = CFG["Cluster"][partition]["GPUS"]
    if max_gpu is not None and int(max_gpu) > 0:
        gpus_per_node = p.fill(
            title = f" Number of GPUs per node: (1≤x≤{int(max_gpu)})",
            default = 1,
            mapper  = int,
            checker = lambda x: 1 <= x <= int(max_gpu),
        )
    else:
        gpus_per_node = None
        
    max_cpu = CFG["Cluster"][partition]["CPUS"]
    if gpus_per_node is not None:
        cpus_per_node = max_cpu * gpus_per_node // max_gpu
    elif node == 1:
        cpus_per_node = p.fill(
            title = f" Number of CPUs per node: (1≤x≤{max_cpu})",
            default = max_cpu,
            mapper  = int,
            checker = lambda x: 1 <= x <= max_cpu,
        )
    else:
        cpus_per_node = max_cpu
    
    if gpus_per_node is not None:
        cpus_per_task = cpus_per_node // gpus_per_node
    else:
        cpus_per_task = p.fill(
            title   = f" Number of CPUs per task: (*factor of {cpus_per_node})",
            default = None,
            mapper  = lambda x: int(x) if x is not None and x.isdigit() else None,
            checker = lambda x: True if x is None else cpus_per_node % x == 0,
        )
        
    run_option = p.select(
        title = " Select the job script template:",
        options = list(run_options.keys()),
        default_option = 0,
    )
    
    run_option = list(run_options.keys())[run_option]
    
    sub_script, job_script = run_options[run_option](
        p = p, 
        partition = partition, 
        nodes = node, 
        cpus_per_node = cpus_per_node, 
        gpus_per_node = gpus_per_node, 
        cpus_per_task = cpus_per_task, 
        timelimit = timelimit.strftime("%d-%H:%M:%S"), 
        qos = qos, 
        user = user, 
        *args, 
        **kwargs)
    
    Path("sub.sh").write_text("\n".join(filter(lambda x: x is not None, sub_script)))
    Path("job.sh").write_text("\n".join(filter(lambda x: x is not None, job_script)))

    print(f"\n Success!")
    sys.exit()
