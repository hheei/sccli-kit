import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from ..const import config_path

def run_gen_user_info():
    if (config_path).exists():
        check_old = config_path.with_suffix(".old")
        i = 1
        while check_old.exists():
            check_old = check_old.with_suffix(f".old{i}")
            i += 1

        import shutil
        shutil.copy(config_path, check_old)

    DEFAULT_CONFIG = f"""# -*- mode: toml -*-
# Sccli-Kit Configuration File

[ Users ]
# Example of user information.
#
#  [ Users.alice ]               ### Your account name
#  name  = "Alice"               ### Your account name
#  short = ["MrA"]               ### Used in the command line
#  root  = "~"                   ### Root directory for user
#  info  = "I Love Python"       ### Some information about you
#
# -*- {{{{ $AUTO_GENERATED_USER_INFO }}}} -*- #

[ Cluster ]
# Define the cluster information. 
# Generated after initial run.
#
# [ Cluster.debug ]
#  NODES     = 4
#  CPUS      = 64
#  GPUS      = 4
#  QOS       = []
#  TIMELIMIT = "1-00:00:00"
#
# -*- {{{{ $AUTO_GENERATED_SLURM_INFO }}}} -*- #
"""
    DEFAULT_CONFIG = DEFAULT_CONFIG.replace(
        "# -*- {{ $AUTO_GENERATED_USER_INFO }} -*- #", generate_default_userinfo() + "\n# -*- {{ $AUTO_GENERATED_USER_INFO }} -*- #")
    DEFAULT_CONFIG = DEFAULT_CONFIG.replace(
        "# -*- {{ $AUTO_GENERATED_SLURM_INFO }} -*- #", generate_slurm_info())

    with open(config_path, "w") as f:
        f.write(DEFAULT_CONFIG)


def generate_slurm_info():
    import subprocess
    import re
    import os
    import pwd
    import grp

    DEBUG_INFO = {"debug": {"NODES": 4, "CPUS": 64,
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

    out = []
    for key, value in partitions.items():
        out.append(f"[ Cluster.{key} ]")
        out.append(f"NODES     = {value['NODES']}")
        out.append(f"CPUS      = {value['CPUS']}")
        out.append(f"GPUS      = {value['GPUS']}")
        out.append(f"QOS       = {value['QOS']}")
        out.append(f"TIMELIMIT = \"{value['TIMELIMIT']}\"")
        out.append(f"")
    
    return "\n".join(out)


def generate_default_userinfo():
    import os

    # Get current username
    current_user = os.getenv('USER') or os.getenv('LOGNAME') or 'Alice'

    USER_INFO = {
        current_user: {
            "name": current_user,
            "short": [current_user[:5].upper()],
            "root": Path.home(),
            "info": "Default User"
        }
    }

    out = []
    for key, value in USER_INFO.items():
        out.append(f"[ Users.{key} ]")
        out.append(f"name  = \"{key}\"")
        out.append(f"short = {value['short']}")
        out.append(f"root  = \"{value['root']}\"")
        out.append(f"info  = \"{value['info']}\"")
        out.append(f"")
    return "\n".join(out)

if not (config_path).exists():
    run_gen_user_info()
    
with open(config_path, "rb") as f:
    CFG = tomllib.load(f)