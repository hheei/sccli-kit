import socket
import sys
import os
from datetime import datetime
from pathlib import Path

from scck.const import cmdlen
from scck.fn import prompt, is_option_yes

cluster_info = {
    # WM1
    "wm1": {
        "C032M0128G": {
            "N": 120,
            "cpu": 32,
            "gpu": None,
            "qos": ["low","normal","high"],
            "time": None
        },
        "C032M0256G": {
            "N": 46,
            "cpu": 32,
            "gpu": None,
            "qos": ["low","normal","high"],
            "time": None
        },
        "C032M0512G": {
            "N": 4,
            "cpu": 32,
            "gpu": None,
            "qos": ["low","normal","high"],
            "time": None
        },

        "GPU": {
            "N": 10,
            "cpu": 12,
            "gpu": 2,
            "qos": ["low","normal","high"],
            "time": None
        },
        "GPU36": {
            "N": 5,
            "cpu": 36,
            "gpu": 4,
            "qos": ["low","normal","high"],
            "time": None
        },  
    },
    
    # WM2
    "wm2": {
        "C064M0256G": {
            "N": 259,
            "cpu": 64,
            "gpu": None,
            "qos": ["low","normal","high"],
            "time": "5-00:00:00",
        },
        "C064M1024G": {
            "N": 48,
            "cpu": 64,
            "gpu": None,
            "qos": ["low","normal","high"],
            "time": "5-00:00:00",
        },
        "GPU40G": {
            "N": 5,
            "cpu": 64,
            "gpu": 4,
            "qos": ["low","normal","high"],
            "time": "5-00:00:00",
        },
        "GPU80G": {
            "N": 10,
            "cpu": 64,
            "gpu": 4,
            "qos": ["low","normal","high"],
            "time": "5-00:00:00",
        },
    },
    
    # NSCC
    "th-hpc4": {
        "debug": {
            "N": 4,
            "cpu": 36,
            "gpu": None,
            "qos": None,
            "time": "00:30:00",
        },
        "short2": {
            "N": 250,
            "cpu": 36,
            "gpu": None,
            "qos": None,
            "time": "2-00:00:00",
        },
        "long2": {
            "N": 250,
            "cpu": 36,
            "gpu": None,
            "qos": None,
            "time": "10-00:00:00",
        },
        "cp3": {
            "N": 20,
            "cpu": 36,
            "gpu": None,
            "qos": None,
            "time": None,
        },
        "gpu": {
            "N": 8,
            "cpu": 36,
            "gpu": 1,
            "qos": None,
            "time": None,
        }
    }
}

def run_genjob():
    print(" ", end="")
    print(" Job Generator ".center(cmdlen, "="))
    cluster = socket.getfqdn()
    for c_name, c_info in cluster_info.items():
        if c_name in cluster:
            break
    else:
        pass
        # raise ValueError(f"Cluster `{cluster}` not found in cluster_info")
            
    # Partition
    partion = list(c_info.keys())[0]
           
    cmd = prompt(f" Select the partition:\n{chr(10).join([' {}) {}'.format(i, p) for i, p in enumerate(list(c_info.keys()))])}\n\n q) Exit\n b) Back\n ----->\n")
    
    if cmd == "b":
        return True
    elif cmd == "q":
        sys.exit()
    elif cmd != "":
        assert cmd.isdigit() and 0 <= int(cmd) < len(list(c_info.keys())), f"Invalid partition index: {cmd}!"
        partion = list(c_info.keys())[int(cmd)]

    # Quality of service
    qos = None
    
    if c_info[partion]["qos"] is not None:
        cmd = prompt(f" Select the quality of service:\n{chr(10).join([' {}) {}'.format(i, q) for i, q in enumerate(c_info[partion]['qos'])])}\n Q) Exit\n B) Back\n ----->\n")
        
        if cmd == "b":
            return True
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(c_info[partion]["qos"]), f"Invalid quality of service index: {cmd}!"
            qos = c_info[partion]["qos"][int(cmd)]
    
    # Time
    time = "1-00:00:00"
    
    if c_info[partion]["time"] is not None:
        cmd = prompt(f" Task running time ( <{c_info[partion]['time']} )\n Format: d-HH:MM:SS\n ----->\n")
        
        if cmd != "":
            _cmd = datetime.strptime(cmd, "%d-%H:%M:%S" if "-" in cmd else "%H:%M:%S")
            _t = datetime.strptime(c_info[partion]["time"], "%d-%H:%M:%S" if "-" in c_info[partion]["time"] else "%H:%M:%S")
            assert _cmd < _t, f"Invalid time: {cmd}!"
            time = _cmd.strftime("%d-%H:%M:%S") if _cmd < _t else _t.strftime("%d-%H:%M:%S")
    
    # Node
    node = 1

    cmd = prompt(f" Number of nodes ( ≤{c_info[partion]['N']} )\n ----->\n")
    
    if cmd != "":
        assert cmd.isdigit() and 0 < int(cmd) <= c_info[partion]["N"], f"Invalid node index: {cmd}!"
        node = int(cmd)
    
    # GPU
    gpu = None
    
    if c_info[partion]['gpu'] is not None:
        cmd = prompt(f" Number of GPUs ( ≤{c_info[partion]['gpu']} )\n ----->\n")
    
        if cmd != "":
            assert cmd.isdigit() and 0 < int(cmd) <= c_info[partion]["gpu"], f"Invalid GPU index: {cmd}!"
            gpu = int(cmd)
    
    # CPU
    if gpu is None:
        cpu = c_info[partion]["cpu"]
        
        cmd = prompt(f" Number of CPUs ( ≤{c_info[partion]['cpu']} )\n ----->\n")
    
        if cmd != "":
            assert cmd.isdigit() and 0 < int(cmd) <= c_info[partion]["cpu"], f"Invalid CPU index: {cmd}!"
            cpu = int(cmd)
    else:
        cpu = c_info[partion]["cpu"] // c_info[partion]["gpu"] * gpu    
        
    JOB_NAME = f"{os.environ.get("USER")[:5] or os.environ.get("USERNAME")[:5]}-$now"
    JOB_DIR = Path.home() / ".jobs"
    
    job_script = [
        "#!/bin/bash",
        f"#SBATCH --partition={partion}",
        None if qos is None else f"#SBATCH --qos={qos}",
        f"#SBATCH --nodes={node}",
        f"#SBATCH -c {cpu}",
        None if gpu is None else f"#SBATCH --gres=gpu:{gpu}",
        f"#SBATCH --time={time}",
        "#SBATCH --output=job.%j.out",
        "#SBATCH --error=job.%j.err",
        "",
        "source ~/.bashrc",
        "module purge",
        "cd ${SLURM_SUBMIT_DIR}",
        f"ln -s {JOB_DIR}/${{SLURM_JOB_NAME}}/job.${{SLURM_JOB_ID}}.out ${{SLURM_SUBMIT_DIR}}",
        f"ln -s {JOB_DIR}/${{SLURM_JOB_NAME}}/job.${{SLURM_JOB_ID}}.err ${{SLURM_SUBMIT_DIR}}",
        "",
    ]
    
    # Run script
    run_options = {
        "vasp": lambda: run_vasp_template(node, cpu),
        "ppafm": lambda: run_ppafm_template(node, cpu),
    }
    
    sub_script = [ 'now=$(date +%Y%m%d-%H%M%S)', 
                   'sbatch \\',
                  f'    --job-name=\"{JOB_NAME}\" \\',
                  f'    --chdir={JOB_DIR}/$now \\',
                   '    job.sh']
    
    cmd = prompt(f" Select run script templates\n{chr(10).join([' {}) {}'.format(i, r) for i, r in enumerate(run_options.keys())])}\n\n q) Exit\n b) Back\n ----->\n")
        
    if cmd == "b":
        return
    elif cmd == "q":
        sys.exit()
    
    if cmd != "":
        assert cmd.isdigit() and 0 <= int(cmd) < len(run_options.keys()), f"Invalid run script template index: {cmd}!"
        extra_sub_script, extra_job_script = run_options[list(run_options.keys())[int(cmd)]]()
        sub_script.extend(extra_sub_script)
        job_script.extend(extra_job_script)
        
    with open(Path().cwd() / "sub.sh", "w") as f:
        f.write("\n".join(filter(lambda x: x is not None, sub_script)))
        f.write("\n")
    
    with open(Path().cwd() / "job.sh", "w") as f:
        f.write("\n".join(filter(lambda x: x is not None, job_script)))
        f.write("\n")
        
    print(f"\n Success!")
    sys.exit()
        
def run_vasp_template(node, cpu):
    import subprocess
    import re
    
    try:
        result = subprocess.run("module avail 2>&1", shell=True, text=True, capture_output=True)
        output = result.stdout + result.stderr

        vasp_modules = re.findall(r'vasp/\S+', output)

        if len(vasp_modules) == 0:
            vasp_name = "vasp"
            print(" Warning: No vasp module found, fallback to `module add vasp`")
        elif len(vasp_modules) == 1:
            vasp_name = vasp_modules[0]
            print(f" Found only one vasp module: {vasp_name}")
        else:
            cmd = prompt(f" Select the vasp module:\n{chr(10).join([' {}) {}'.format(i, m) for i, m in enumerate(vasp_modules)])}\n\n q) Exit\n b) Back\n ----->\n")
            
            if cmd == "b":
                return
            elif cmd == "q":
                sys.exit()
            elif cmd != "":
                assert cmd.isdigit() and 0 <= int(cmd) < len(vasp_modules), f"Invalid vasp module index: {cmd}!"
                vasp_name = vasp_modules[int(cmd)]
            
    except Exception as e:
        print(e)
        vasp_name = "vasp"
    
    sub_script = []
    
    job_script = [f"ulimit -Ss unlimited",
                  f"module add {vasp_name}",
                  f"OMP_NUM_THREADS=1 mpirun -np {node * cpu} vasp_std"]
    
    return sub_script, job_script

def run_ppafm_template(node, cpu):    
    import os
    assert node == 1, "ppafm only supports single node"
    
    cmd = prompt.last_cmd
    
    CONDA_PATH = Path(os.environ.get("CONDA_PREFIX"))
    
    avail_envs = ["base"] + list(e.name for e in CONDA_PATH.glob("envs/*") if e.is_dir())
    if (Path() / ".venv").exists():
        avail_envs.append(".venv")
    
    cmd = prompt(f" Select the python environment:\n{chr(10).join([' {}) {}'.format(i, e) for i, e in enumerate(avail_envs)])}\n\n q) Exit\n b) Back\n ----->\n")
    
    if cmd == "b":
        return
    elif cmd == "q":
        sys.exit()
    elif cmd != "":
        assert cmd.isdigit() and 0 <= int(cmd) < len(avail_envs), f"Invalid environment index: {cmd}!"
        env_name = avail_envs[int(cmd)]
    
    STRUCTURE_FILE = [p for p in Path().glob("*") if p.is_file() and str(p).endswith(("LOCPOT", ".xsf", ".poscar", ".xyz", ".cif"))]
    
    if len(STRUCTURE_FILE) == 0:
        raise ValueError("No structure file found, Must be one of the following: LOCPOT, .xsf, .poscar, .xyz, .cif")
    elif len(STRUCTURE_FILE) == 1:
        stru = STRUCTURE_FILE[0]
        print(f"Found only one structure file: {STRUCTURE_FILE[0]}")
    else:
        cmd = prompt(f" Select the structure file:\n{chr(10).join([' {}) {}'.format(i, s) for i, s in enumerate(STRUCTURE_FILE)])}\n\n q) Exit\n b) Back\n ----->\n")
        
        if cmd == "b":
            return
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(STRUCTURE_FILE), f"Invalid structure file index: {cmd}!"
            stru = STRUCTURE_FILE[int(cmd)]
    
    PLOT_ATOM = False
    
    if stru.suffix not in (".xsf", "LOCPOT"):
        cmd = prompt(f" Plot Atoms on images: (default: no)\n ----->\n")
        
        if is_option_yes(cmd):
            PLOT_ATOM = True
    
    if env_name == ".venv":
        job_script = [f"source .venv/bin/activate"]
    else:
        job_script = [f"mamba activate {env_name}"]
    
    job_script.append(f"export OMP_NUM_THREADS={cpu}")
    
    if str(stru).endswith(("LOCPOT", ".xsf")):
        job_script.append(f"ppafm-generate-elff -i {stru} -F xsf -t dz2 -f npy")
        job_script.append(f"ppafm-generate-ljff -i {stru} -F xsf -f npy")
        job_script.append(f"ppafm-relaxed-scan -k 0.25 -q -0.1 --pos -f npy")
        job_script.append(f"ppafm-plot-results --arange 2.0 4.0 2 --df --cbar -f npy {'--atoms' if PLOT_ATOM else ''}")
    else:
        job_script.append(f"ppafm-generate-elff-point-charges -i {stru} -f npy")
        job_script.append(f"ppafm-generate-ljff -i {stru} -f npy")
        job_script.append(f"ppafm-relaxed-scan -k 0.25 -q -0.1 --pos -f npy")
        job_script.append(f"ppafm-plot-results --arange 2.0 4.0 2 --df --cbar -f npy {'--atoms' if PLOT_ATOM else ''}")
            
    return [], job_script

def run_lammps_template(node, cpu, gpu):
    pass