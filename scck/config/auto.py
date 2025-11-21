import json
import subprocess
import re
import os
import pwd
import grp

from pathlib import Path
from scck.const import config_path

def update_user_info(*args, **kwargs):
    if not config_path.exists():
        config = {
            "Config": {
                "user_mode": "local",
                "job_log_dir": "~/.jobs"
            },
            "Users": {},
            "Cluster": {},
            "Modules": {}
        }
    else:
        config = json.loads(config_path.read_text())
        
    config = check_default_user(config)
    config = check_slurm_info(config)
    config_path.write_text(json.dumps(config, indent=4, ensure_ascii=False))
    return config

def check_default_user(config):
    current_user = os.getenv('USER') or os.getenv('LOGNAME')
    
    if current_user is None:
        pass
    
    if current_user not in config['Users']:
        config['Users'][current_user] = {
            "name": current_user,
            "short": [current_user[:5].upper()],
            "root": str(Path.home().expanduser()),
            "info": "Default User"
        }
    
    return config

def check_slurm_info(config):
    DEBUG_INFO = {"_debug": {"NODES": 4, "CPUS": 64,
                            "GPUS": 4, "QOS": [], "TIMELIMIT": "1-00:00:00"}}

    # Get current username
    current_user = pwd.getpwuid(os.getuid()).pw_name
    user_groups = tuple(grp.getgrgid(gid).gr_name for gid in os.getgroups())
    
    try:
        lines = subprocess.run(
            ["sinfo", "-o", "%P %D %c %G %l", "--noheader"],
            capture_output=True, text=True, check=True
        ).stdout.strip().splitlines()

        perm = subprocess.run(
            ["scontrol", "show", "partition"],
            capture_output=True, text=True, check=True
        ).stdout.strip().split("PartitionName=")[1:]
        
        qos_query = subprocess.run(
            ["sacctmgr", "show", "qos", "-P", "-n", "format=name,Priority"],
            capture_output=True, text=True, check=True
        ).stdout.strip().splitlines()
        qos_priority = {i.split("|")[0]: float(i.split("|")[1]) for i in qos_query}

    except (FileNotFoundError, subprocess.CalledProcessError):
        partitions = DEBUG_INFO

    else:
        lines = list(filter(None, map(lambda x: x.strip().replace(
            "*", ""), lines)))
        avaliable_partitions = {}
        for gp_lines in perm:
            gp_lines = gp_lines.splitlines()
            gp_name = gp_lines[0]
            gp_dict = {}
            for key_lines in gp_lines[1:]:
                key_lines = key_lines.strip().split()
                for key_value in key_lines:
                    key_value = key_value.split("=")    
                    if len(key_value) == 2:
                        gp_dict[key_value[0]] = key_value[1]
            
            if any(i in tuple(gp_dict.get('AllowAccounts', '').split(',')) for i in user_groups):
                avaliable_partitions[gp_name.upper()] = gp_dict
        
        partitions = {}
        for i, line in enumerate(lines):
            line = line.split()
            # Only process partitions where user has permission
            if line[0].upper() in avaliable_partitions.keys():
                # Get number of nodes for this partition
                total_nodes = 1
                if line[1] != "(null)" and line[1] != "N/A":
                    node_match = re.search(r'(\d+)', line[1])
                    total_nodes = int(node_match.group(1)) if node_match else 1

                # Parse CPU information
                cpus_per_node = 1
                if line[2] != "(null)" and line[2] != "N/A":
                    # Parse CPU info like "64/64" (allocated/total)
                    cpu_match = re.search(r'(\d+)', line[2])
                    if cpu_match:
                        cpus_per_node = int(cpu_match.group(1))

                # Parse GPU information
                gpu_count = 0
                if line[3] != "(null)" and line[3] != "N/A":
                    # Extract number from formats like ":4", ":2*", etc.
                    gpu_match = re.search(r':(\d+)', line[3])
                    if gpu_match:
                        gpu_count = int(gpu_match.group(1))

                # Get QOS for this partition
                qos = avaliable_partitions[line[0].upper()].get('AllowQos', 'ALL')

                if qos in ["ALL", "N/A"]:
                    qos = []
                else:
                    qos = qos.split(',')
                    qos = sorted(qos, key=lambda x: qos_priority[x])
                
                partitions[line[0]] = {
                    "NODES": total_nodes,
                    "CPUS": cpus_per_node,
                    "GPUS": gpu_count,
                    "QOS": qos,
                    "TIMELIMIT": line[4]  # Default value
                }
    
    for name, value in partitions.items():
        if name not in config['Cluster']:
            config['Cluster'][name] = value
    
    return config