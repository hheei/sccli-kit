import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

from scck.const import cmdlen
from scck.fn import prompt, get_python_venv
from scck.info import CFG


def run_genjob():
    print(" ", end="")
    print(" Job Generator ".center(cmdlen, "="))

    if len(CFG['Users'].keys()) == 1:
        user = list(CFG['Users'].keys())[0]
    else:
        cmd = prompt(
            f" Select the user:\n{chr(10).join([' {}) {}'.format(i, u) for i, u in enumerate(list(CFG['Users'].keys()))])}\n\n q) Exit\n b) Back\n ----->\n")

        if cmd == "b":
            return True
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(
                list(CFG['Users'].keys())), f"Invalid user index: {cmd}!"
            user = list(CFG['Users'].keys())[int(cmd)]

    partitions = CFG["Cluster"]

    partion = list(partitions.keys())[0]

    cmd = prompt(
        f" Select the partition:\n{chr(10).join([' {}) {}'.format(i, p) for i, p in enumerate(list(partitions.keys()))])}\n\n q) Exit\n b) Back\n ----->\n")

    if cmd == "b":
        return True
    elif cmd == "q":
        sys.exit()
    elif cmd != "":
        assert cmd.isdigit() and 0 <= int(cmd) < len(
            list(partitions.keys())), f"Invalid partition index: {cmd}!"
        partion = list(partitions.keys())[int(cmd)]

    # Quality of service
    qos = None

    if partitions[partion]["QOS"]:
        if len(partitions[partion]["QOS"]) == 1:
            qos = partitions[partion]["QOS"][0]
        else:
            cmd = prompt(
                f" Select the quality of service:\n{chr(10).join([' {}) {}'.format(i, q) for i, q in enumerate(partitions[partion]['QOS'])])}\n\n q) Exit\n b) Back\n ----->\n")

            if cmd == "b":
                return True
            elif cmd == "q":
                sys.exit()
            elif cmd != "":
                assert cmd.isdigit() and 0 <= int(cmd) < len(
                    partitions[partion]["QOS"]), f"Invalid quality of service index: {cmd}!"
                qos = partitions[partion]["QOS"][int(cmd)]

    # Time
    time = "1-00:00:00"

    if partitions[partion]["TIMELIMIT"] is not None:
        cmd = prompt(
            f" Task running time ( <{partitions[partion]['TIMELIMIT']} )\n Format: d-HH:MM:SS\n ----->\n")

        if cmd != "":
            _cmd = datetime.strptime(
                cmd, "%d-%H:%M:%S" if "-" in cmd else "%H:%M:%S")
            _t = datetime.strptime(
                partitions[partion]["TIMELIMIT"], "%d-%H:%M:%S" if "-" in partitions[partion]["TIMELIMIT"] else "%H:%M:%S")
            assert _cmd < _t, f"Invalid time: {cmd}!"
            time = _cmd.strftime(
                "%d-%H:%M:%S") if _cmd < _t else _t.strftime("%d-%H:%M:%S")

    # Node
    node = 1

    cmd = prompt(
        f" Number of nodes ( ≤{partitions[partion]['NODES']} )\n ----->\n")

    if cmd != "":
        assert cmd.isdigit() and 0 < int(
            cmd) <= partitions[partion]["NODES"], f"Invalid node index: {cmd}!"
        node = int(cmd)

    # GPU
    gpu = None

    if partitions[partion]['GPUS'] is not None:
        if partitions[partion]['GPUS'] != 0:
            cmd = prompt(
                f" Number of GPUs ( ≤{partitions[partion]['GPUS']} )\n ----->\n")

            if cmd != "":
                assert cmd.isdigit() and 0 < int(
                    cmd) <= partitions[partion]["GPUS"], f"Invalid GPU index: {cmd}!"
                gpu = int(cmd)

    # CPU
    if gpu is None:
        cpu = partitions[partion]["CPUS"]

        cmd = prompt(
            f" Number of CPUs ( ≤{partitions[partion]['CPUS']} )\n ----->\n")

        if cmd != "":
            assert cmd.isdigit() and 0 < int(
                cmd) <= partitions[partion]["CPUS"], f"Invalid CPU index: {cmd}!"
            cpu = int(cmd)
    else:
        cpu = partitions[partion]["CPUS"] // partitions[partion]["GPUS"] * gpu

    JOB_NAME = f"{CFG['Users'][user]['short'][0]}-$now"
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
        "lammps": lambda: run_lammps_template(node, cpu, gpu),
    }

    sub_script = ['now=$(date +%Y%m%d-%H%M%S)',
                  'sbatch \\',
                  f'    --job-name=\"{JOB_NAME}\" \\',
                  f'    --chdir={JOB_DIR}/{JOB_NAME} \\',
                  '    job.sh']

    cmd = prompt(
        f" Select run script templates\n{chr(10).join([' {}) {}'.format(i, r) for i, r in enumerate(run_options.keys())])}\n\n q) Exit\n b) Back\n ----->\n")

    if cmd == "b":
        return
    elif cmd == "q":
        sys.exit()

    if cmd != "":
        assert cmd.isdigit() and 0 <= int(cmd) < len(run_options.keys()
                                                     ), f"Invalid run script template index: {cmd}!"
        extra_sub_script, extra_job_script = run_options[list(run_options.keys())[
            int(cmd)]]()
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
        result = subprocess.run("module avail 2>&1",
                                shell=True, text=True, capture_output=True)
        output = result.stdout + result.stderr

        vasp_modules = re.findall(r'vasp/\S+', output)

        if len(vasp_modules) == 0:
            vasp_name = "vasp"
            print(" Warning: No vasp module found, fallback to `module add vasp`")
        elif len(vasp_modules) == 1:
            vasp_name = vasp_modules[0]
            print(f" Found only one vasp module: {vasp_name}")
        else:
            cmd = prompt(
                f" Select the vasp module:\n{chr(10).join([' {}) {}'.format(i, m) for i, m in enumerate(vasp_modules)])}\n\n q) Exit\n b) Back\n ----->\n")

            if cmd == "b":
                return
            elif cmd == "q":
                sys.exit()
            elif cmd != "":
                assert cmd.isdigit() and 0 <= int(cmd) < len(
                    vasp_modules), f"Invalid vasp module index: {cmd}!"
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
    assert node == 1, "PPAFM only supports single node"

    cmd = prompt.last_cmd

    avail_envs = get_python_venv()
    
    if len(avail_envs["conda"]) == 1 and len(avail_envs["venv"]) == 0:
        print(f" Found only one conda environment: {avail_envs['conda'][0]}")
        env_name = avail_envs["conda"][0]
        USE_CONDA = True
    elif len(avail_envs["conda"]) == 0 and len(avail_envs["venv"]) == 1:
        print(f" Found only one venv environment: {avail_envs['venv'][0]}")
        env_name = avail_envs["venv"][0]
        USE_CONDA = False
    elif len(avail_envs["conda"]) == 0 and len(avail_envs["venv"]) == 0:
        print(" Warning: No python environment found, no venv will be used")
        env_name = ".venv"
        USE_CONDA = False
    else:
        envs = avail_envs["conda"] + avail_envs["venv"]
        print(" Select the python environment:")
        if len(avail_envs["conda"]) > 0:
            print(" --> CONDA <--")
            print("\n".join([f" {i}) {envs[i]}" for i in range(len(avail_envs["conda"]))]))
        if len(avail_envs["venv"]) > 0:
            print(" --> VENV <--")
            print("\n".join([f" {i}) {envs[i]}" for i in range(len(avail_envs["venv"]))]))
        print("\n q) Exit\n b) Back\n ----->\n")
        
        cmd = prompt("")
    
        if cmd == "b":
            return
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(envs), f"Invalid environment index: {cmd}!"
            cmd = int(cmd)
            env_name = envs[cmd]
            USE_CONDA = cmd < len(avail_envs["conda"])

    STRUCTURE_FILE = [p for p in Path().glob("*") if p.is_file()
                      and str(p).endswith(("LOCPOT", ".xsf", ".poscar", ".xyz", ".cif"))]
    
    if len(STRUCTURE_FILE) == 0:
        raise ValueError(
            "No structure file found, Must be one of the following: LOCPOT, .xsf, .poscar, .xyz, .cif")
                
    elif len(STRUCTURE_FILE) == 1:
        stru = STRUCTURE_FILE[0]
        print(f"Found structure file: {STRUCTURE_FILE[0]}")
    else:
        cmd = prompt(
            f" Select the structure file:\n{chr(10).join([' {}) {}'.format(i, s) for i, s in enumerate(STRUCTURE_FILE)])}\n\n q) Exit\n b) Back\n ----->\n")

        if cmd == "b":
            return
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(
                STRUCTURE_FILE), f"Invalid structure file index: {cmd}!"
            stru = STRUCTURE_FILE[int(cmd)]

    if stru.name == "LOCPOT":
        print(" LOCPOT detected, converting to XSF...")
        try:
            subprocess.run(["v2xsf", stru, "-d"], check = True, cwd = str(Path().cwd()))
            stru = stru.with_suffix(".xsf")
            print(f" Converted LOCPOT to XSF: {stru}")
        except Exception as e:
            print(f" Failed to convert LOCPOT to XSF.")
            raise e
        
    if env_name is not None and USE_CONDA:
        job_script = [f"conda activate {env_name}"]
    elif env_name is not None and not USE_CONDA:
        job_script = [f"source {env_name}/bin/activate"]
    else:
        job_script = []

    job_script.append(f"export OMP_NUM_THREADS={cpu}")

    if str(stru).endswith(".xsf"):
        job_script.append(
            f"ppafm-generate-elff -i {stru} -F xsf -t dz2 -f npy")
        job_script.append(f"ppafm-generate-ljff -i {stru} -F xsf -f npy")
        job_script.append(f"ppafm-relaxed-scan -k 0.25 -q -0.1 --pos -f npy")
        job_script.append(
            f"ppafm-plot-results --arange 2.0 4.0 2 --df --cbar -f npy")
    else:
        job_script.append(
            f"ppafm-generate-elff-point-charges -i {stru} -f npy")
        job_script.append(f"ppafm-generate-ljff -i {stru} -f npy")
        job_script.append(f"ppafm-relaxed-scan -k 0.25 -q -0.1 --pos -f npy")
        job_script.append(
            f"ppafm-plot-results --arange 2.0 4.0 2 --df --cbar -f npy")

    return [], job_script

def run_lammps_template(node, cpu, gpu):
    paths = os.environ["PATH"].split(os.pathsep)
    avail_cmd = []
    for path in paths:
        path = Path(path)
        if path.is_dir() and path.name == "bin":
            for cmd in path.glob("*"):
                if cmd.is_file() and os.access(cmd, os.X_OK) and cmd.name.startswith(("lmp","lammps")):
                    avail_cmd.append(str(cmd))
    
    if len(avail_cmd) == 0:
        cmd = prompt(" No lammps command found, please enter the lammps command:\n ----->\n")
        if cmd == "":
            print(" Using default lammps command: lmp")
            USE_CMD = "lmp"
        else:
            USE_CMD = cmd
            
    elif len(avail_cmd) == 1:
        USE_CMD = avail_cmd[0]
        print(f" Found lammps command: {USE_CMD}")
        
    else:
        cmd = prompt(
            f" Select lammps command:\n{chr(10).join([' {}) {}'.format(i, q) for i, q in enumerate(avail_cmd)])}\n\n q) Exit\n b) Back\n ----->\n")

        if cmd == "b":
            return
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(avail_cmd), f"Invalid lammps command index: {cmd}!"
            USE_CMD = avail_cmd[int(cmd)]
    
    if node == 1:
        OMP_NUM_THREADS = cpu
    else:
        cmd = prompt(f" Please set OMP_NUM_THREADS ( ≤ {cpu} )\n ----->\n")
        if cmd != "":
            assert cmd.isdigit() and 0 < int(cmd) <= cpu, f"Invalid OMP_NUM_THREADS: {cmd}!"
            OMP_NUM_THREADS = int(cmd)
        else:
            OMP_NUM_THREADS = 1
    
    job_script = [f"export OMP_NUM_THREADS={OMP_NUM_THREADS}"]
    
    CONDA_PATH = Path(os.environ.get("CONDA_EXE", "")).parent.parent
    if USE_CMD.startswith(str(CONDA_PATH)):
        job_script.append(f"conda activate {USE_CMD.replace(str(CONDA_PATH), "").lstrip("/").split("/")[0]}")
    
    if gpu is None and OMP_NUM_THREADS > 1:
        prefix = "-sf omp"
    elif gpu is not None:
        prefix = "-sf gpu"
    else:
        prefix = ""
        
    input_files = [p for p in Path().glob("*") if p.is_file() and p.stem in ("in", "input")]
    
    if len(input_files) == 0:
        cmd = prompt(" No input file found, please specify the input file:\n ----->\n")
        if cmd == "":
            print(" Using default input file: in.lmp")
            IN_CMD = "-in in.lmp"
        else:
            IN_CMD = f"-in {cmd}"
            
    elif len(input_files) == 1:
        IN_CMD = f"-in {input_files[0]}"
        print(f" Found input file: {input_files[0]}")
    
    else:
        cmd = prompt(
            f" Select the input file:\n{chr(10).join([' {}) {}'.format(i, s) for i, s in enumerate(input_files)])}\n\n q) Exit\n b) Back\n ----->\n")
            
        if cmd == "b":
            return
        elif cmd == "q":
            sys.exit()
        elif cmd != "":
            assert cmd.isdigit() and 0 <= int(cmd) < len(input_files), f"Invalid input file index: {cmd}!"
            IN_CMD = f"-in {input_files[int(cmd)]}"
            
    if node > 1:
        if node * cpu % OMP_NUM_THREADS > 0:
            print(f" Warning: {node * cpu} CPUs is not divisible by {OMP_NUM_THREADS}, some CPUs will be wasted!")
        job_script.append(f"mpirun -np {node * cpu // OMP_NUM_THREADS} {USE_CMD} {prefix} {IN_CMD}")
    else:
        job_script.append(f"{USE_CMD} {prefix} {IN_CMD}")
        
    return [], job_script