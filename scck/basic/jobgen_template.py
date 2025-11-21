import os
import sys
import subprocess
from pathlib import Path

from scck.fn import Prompt
from scck.config import CFG

def job_empty_template(p: Prompt, partition, nodes, cpus_per_node, gpus_per_node, cpus_per_task, timelimit, qos, *args, **kwargs):
    if cpus_per_task is None:
        ntasks = nodes * cpus_per_node
        cpus_per_task = 1
    else:
        ntasks = nodes * cpus_per_node // cpus_per_task
        
    job_script = [
         "#!/bin/bash",
        f"#SBATCH --job-name=UNK-JOB",
        f"#SBATCH --partition={partition}",
        f"#SBATCH --nodes={nodes}",
        f"#SBATCH --ntasks={ntasks}",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --gpus-per-node={gpus_per_node}" if gpus_per_node is not None else None,
        f"#SBATCH --time={timelimit}",
        f"#SBATCH --qos={qos}" if qos is not None else None,
         "#SBATCH --output=slurm-%j.out",
         "#SBATCH --error=slurm-%j.err",
         "if [ -z \"${SLURM_JOB_ID}\" ]; then",
         "    echo \"\${SLURM_JOB_ID} is not set.\"",
         "    echo \"Either \`sbatch job.sh\` or \`bash sub.sh\` to submit the job.\"",
         "    exit 1",
         "fi",
         "",
         "source ~/.bashrc",
         "module purge",
         "cd ${SLURM_SUBMIT_DIR}",
         "scck job init",
         "",
         "export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}",
         "mpirun -np $SLURM_NTASKS bash -c 'echo \"Rank ${OMPI_COMM_WORLD_RANK} on $(hostname)\"'"]

    sub_script = [
        "JOB_NAME=`scck job user`",
        "sbatch \\",
        "    --job-name=\"$JOB_NAME\" \\",
        "    job.sh"
    ]
    
    return sub_script, job_script

def job_vasp_template(p: Prompt, partition, nodes, cpus_per_node, gpus_per_node, cpus_per_task, timelimit, qos, *args, **kwargs):
    if cpus_per_task is None:
        ntasks = nodes * cpus_per_node
        cpus_per_task = 1
    else:
        ntasks = nodes * cpus_per_node // cpus_per_task
        
    vasp_modules = list(filter(
        lambda x: CFG["Modules"][x]["package"] == "vasp", CFG["Modules"].keys()))
    
    if len(vasp_modules) == 0:
        print(" No vasp module found. Fallback to `module add vasp`")
        vasp_cfg = {"package": "vasp", "flags": "module;", "required": "vasp", "src": ""}
    
    elif len(vasp_modules) == 1:
        vasp_name = vasp_modules[0]
        print(f" Found only one vasp module: {vasp_name}")
        vasp_cfg = CFG["Modules"][vasp_name]
    else:
        cmd = p.select(
            title = " Select the vasp module:",
            options = vasp_modules,
            default_option = 0,
        )
        vasp_name = vasp_modules[cmd]
        vasp_cfg = CFG["Modules"][vasp_name]
    
    flags = vasp_cfg["flags"].split(";")
    
    if "module" in flags:
        required = f"module add {vasp_cfg['required']}"
    elif "conda" in flags:
        required = f"conda activate {vasp_cfg['required']}"
    else:
        required = None    
    
    src = vasp_cfg["src"]
    
    job_script = [
         "#!/bin/bash",
        f"#SBATCH --job-name=UNK-JOB",
        f"#SBATCH --partition={partition}",
        f"#SBATCH --nodes={nodes}",
        f"#SBATCH --ntasks={ntasks}",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --gpus-per-node={gpus_per_node}" if gpus_per_node is not None else None,
        f"#SBATCH --time={timelimit}",
        f"#SBATCH --qos={qos}" if qos is not None else None,
         "#SBATCH --output=slurm-%j.out",
         "#SBATCH --error=slurm-%j.err",
         "if [ -z \"${SLURM_JOB_ID}\" ]; then",
         "    echo \"\${SLURM_JOB_ID} is not set.\"",
         "    echo \"Either \`sbatch job.sh\` or \`bash sub.sh\` to submit the job.\"",
         "    exit 1",
         "fi",
         "",
         "source ~/.bashrc",
         "module purge",
         "cd ${SLURM_SUBMIT_DIR}",
         "scck job init",
         "",
         required,
         None if src is None else src,
         "ulimit -Ss unlimited",
         "export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}",
         "mpirun -np ${SLURM_NTASKS} vasp_std"]

    sub_script = [
        "JOB_NAME=`scck job user`",
        "sbatch \\",
        "    --job-name=\"$JOB_NAME\" \\",
        "    job.sh"
    ]

    return sub_script, job_script

def job_lammps_template(p: Prompt, partition, nodes, cpus_per_node, gpus_per_node, cpus_per_task, timelimit, qos, *args, **kwargs):
    if cpus_per_task is None:
        ntasks = nodes * cpus_per_node
        cpus_per_task = 1
    else:
        ntasks = nodes * cpus_per_node // cpus_per_task
    
    lammps_modules = list(filter(
        lambda x: CFG["Modules"][x]["package"] == "lammps", CFG["Modules"].keys()))
    
    if len(lammps_modules) == 0:
        print(" No lammps module found. Fallback to `# module add lammps`")
        lammps_cfg = {"package": "lammps", "flags": "module;", "required": "lammps", "src": ""}
    
    elif len(lammps_modules) == 1:
        lammps_name = lammps_modules[0]
        print(f" Found only one lammps module: {lammps_name}")
        lammps_cfg = CFG["Modules"][lammps_name]
    else:
        cmd = p.select(
            title = " Select the vasp module:",
            options = lammps_modules,
            default_option = 0,
        )
        lammps_name = lammps_modules[cmd]
        lammps_cfg = CFG["Modules"][lammps_name]
    
    flags = lammps_cfg["flags"].split(";")
    
    input_files = [p for p in Path().glob("*") if p.is_file() and p.stem in ("in", "input")]
    if len(input_files) == 0:
        in_files = p.fill(
            title = " Please specify the input file:",
            default = "in.lmp",
        )
    elif len(input_files) == 1:
        in_files = input_files[0]
        print(f" Found input file: {in_files}")
    else:
        in_files = p.select(
            title = " Select the input file:",
            options = input_files,
            default_option = 0,
        )
    
    
    if "module" in flags:
        required = f"module add {lammps_cfg['required']}"
    elif "conda" in flags:
        required = f"conda activate {lammps_cfg['required']}"
    else:
        required = None
        
    if gpus_per_node is not None and "gpu" in flags:
        prefix = "-sf gpu"
    elif cpus_per_task > 1 and "omp" in flags:
        prefix = "-sf omp"
    else:
        prefix = ""
    
    src = lammps_cfg["src"]
    
    job_script = [
        "#!/bin/bash",
        f"#SBATCH --job-name=UNK-JOB",
        f"#SBATCH --partition={partition}",
        f"#SBATCH --nodes={nodes}",
        f"#SBATCH --ntasks={ntasks}",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --gpus-per-node={gpus_per_node}" if gpus_per_node is not None else None,
        f"#SBATCH --time={timelimit}",
        f"#SBATCH --qos={qos}" if qos is not None else None,
        "#SBATCH --output=slurm-%j.out",
        "#SBATCH --error=slurm-%j.err",
        "if [ -z \"${SLURM_JOB_ID}\" ]; then",
        "    echo \"\${SLURM_JOB_ID} is not set.\"",
        "    echo \"Either \`sbatch job.sh\` or \`bash sub.sh\` to submit the job.\"",
        "    exit 1",
        "fi",
        "",
        "source ~/.bashrc",
        "module purge",
        "cd ${SLURM_SUBMIT_DIR}",
        "scck job init",
        "",
        required,
        None if src is None else src,
        "export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}",
        f"mpirun -np ${{SLURM_NTASKS}} lmp {prefix} -in {in_files}"]

    sub_script = [
        "JOB_NAME=`scck job user`",
        "sbatch \\",
        "    --job-name=\"$JOB_NAME\" \\",
        "    job.sh"
    ]

    return sub_script, job_script

def job_ppafm_template(p: Prompt, partition, nodes, cpus_per_node, gpus_per_node, cpus_per_task, timelimit, qos, *args, **kwargs):
    assert nodes == 1, "PPAFM only supports single node"
    assert cpus_per_node == cpus_per_task, "PPAFM does not support MPI."
    
    from ase.io import read, write
    from ase import Atoms
    
    ppafm_modules = list(filter(
        lambda x: CFG["Modules"][x]["package"] == "ppafm", CFG["Modules"].keys()))
    
    if len(ppafm_modules) == 0:
        print(" No ppafm module found. Fallback to `module add ppafm`")
        ppafm_cfg = {"package": "ppafm", "flags": "module;", "required": "ppafm", "src": ""}
    elif len(ppafm_modules) == 1:
        ppafm_name = ppafm_modules[0]
        print(f" Found only one ppafm module: {ppafm_name}")
        ppafm_cfg = CFG["Modules"][ppafm_name]
    else:
        cmd = p.select(
            title = " Select the ppafm module:",
            options = ppafm_modules,
            default_option = 0,
        )
        ppafm_name = ppafm_modules[cmd]
        ppafm_cfg = CFG["Modules"][ppafm_name]
    
    flags = ppafm_cfg["flags"].split(";")
    
    if "module" in flags:
        required = f"module add {ppafm_cfg['required']}"
    elif "conda" in flags:
        required = f"conda activate {ppafm_cfg['required']}"
    else:
        required = None
    
    structure_files = [p for p in Path("..").glob("*") if p.is_file()
                      and str(p).endswith(("LOCPOT", "CONTCAR", "POSCAR", ".xsf", ".poscar", ".xyz", ".cif"))]
    
    if len(structure_files) == 0:
        structure = Path(p.fill(
            title = " No structure file found. Please specify the structure file:",
            default = "POSCAR",
        ))
        
    elif len(structure_files) == 1:
        structure = structure_files[0]
    
    else:
        structure = structure_files[(p.select(
            title = " Select the structure file:",
            options = list[map(lambda x: x.name, structure_files)],
            default_option = 0,
        ))]
    
    if structure.name == "LOCPOT":
        import numpy as np
        print(" LOCPOT detected, converting to XSF...")
        try:
            subprocess.run(["v2xsf", structure, "-d"], check = True, cwd = str(Path().cwd()))
            structure = structure.with_suffix(".xsf")
            print(f" Converted LOCPOT to XSF: {structure}")
            flag = 0
            with open("LOCPOT.xsf", "r") as f:
                while flag < 2:
                    line = f.readline()
                    if line.startswith("PRIMVEC"):
                        cell = f.readlines(3)
                        cell = np.array(list(map(lambda x: list(map(float, x.strip().split())), cell)))
                        flag += 1
                        
                    elif line.startswith("PRIMCOORD"):
                        N, _ = f.readline().strip().split()
                        lines = f.readlines(int(N))
                        lines = list(map(lambda x: x.strip().split(), lines))
                        numbers = []
                        positions = []
                        for line in lines:
                            numbers.append(int(line[0]))
                            positions.append(list(map(float, line[1:4])))
                        
                        atoms = Atoms(numbers, positions, cell = cell, pbc = [True, True, True])
                        flag += 1
            
            write("in.xyz", atoms, format = "extxyz")
            
        except Exception as e:
            print(f" Failed to convert LOCPOT to XSF.")
            raise e
        
    elif structure.suffix in [".xsf", ".poscar", ".xyz", ".cif"] or structure.name in ["CONTCAR", "POSCAR"]:
        print(f" Found structure file: {structure}")
        atoms = read(structure, index = -1)
        write(structure.with_suffix(".xyz"), atoms, format = "extxyz", columns=["symbols", "positions", "charges"])
    
    else:
        raise ValueError(f"Invalid structure file: {structure}")
    
    Path("params.ini").write_text(
        "probeType   8               # atom type of ProbeParticle (to choose L-J potential ),e.g. 8 for CO, 54 for Xe\n"\
        "tip         'dz2'           # multipole of the PP {'dz2' is the most popular now}, charge cloud is not tilting\n"\
        "sigma       0.71            # FWHM of the gaussian charge cloud {0.7 or 0.71 are standarts}\n"\
        "Amplitude   4.0             # [Å] oscillation amplitude for conversion Fz->df\n"\
        "charge      -0.1            # effective charge of probe particle [e]\n"\
        "klat        0.75            # [N/m] harmonic spring potential (x,y) components, x,y is bending stiffnes\n"\
        "krad        20.00           # [N/m] harmonic spring potential R component, R is the particle-tip bond-length stiffnes\n"\
        "r0Probe     0.0 0.0  4.00   # [Å] equilibirum position of probe particle (x,y,R) components, R is bond length, x,y introduce tip asymmetry\n"\
        "PBC         True            # Periodic boundary conditions ? [ True/False ]\n"\
        f"gridA       {atoms.cell[0][0]:.6f} {atoms.cell[0][1]:.6f} {atoms.cell[0][2]:.6f}\n"\
        f"gridB       {atoms.cell[1][0]:.6f} {atoms.cell[1][1]:.6f} {atoms.cell[1][2]:.6f}\n"\
        f"gridC       {atoms.cell[2][0]:.6f} {atoms.cell[2][1]:.6f} {atoms.cell[2][2]:.6f}\n"\
        "scanMin      0.0    0.0     6.0         # start of scanning (x,y,z)\n"\
        "scanMax     20.0   20.0    14.0         # end of scanning (x,y,z)\n"\
        "scanStep     0.1    0.1    0.02         # step size of scanning (x,y,z)"\
        )
    
    src = ppafm_cfg["src"]
    
    job_script = [
        "#!/bin/bash",
        f"#SBATCH --job-name=UNK-JOB",
        f"#SBATCH --partition={partition}",
        f"#SBATCH --nodes={nodes}",
        f"#SBATCH --ntasks=1",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --gpus-per-node={gpus_per_node}" if gpus_per_node is not None else None,
        f"#SBATCH --time={timelimit}",
        f"#SBATCH --qos={qos}" if qos is not None else None,
        "#SBATCH --output=slurm-%j.out",
        "#SBATCH --error=slurm-%j.err",
        "if [ -z \"${SLURM_JOB_ID}\" ]; then",
        "    echo \"\${SLURM_JOB_ID} is not set.\"",
        "    echo \"Either \`sbatch job.sh\` or \`bash sub.sh\` to submit the job.\"",
        "    exit 1",
        "fi",
        "",
        "source ~/.bashrc",
        "module purge",
        "cd ${SLURM_SUBMIT_DIR}",
        "scck job init",
        "",
        required,
        None if src is None else src,
        "export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK}"]
    
    if structure.name == "LOCPOT":
        job_script.append("ppafm-generate-elff -i LOCPOT.xsf -F xsf -t dz2 -f npy")
    else:
        job_script.append("ppafm-generate-elff-point-charges -i in.xyz -F xyz -t dz2 -f npy")
    
    if structure.name == "LOCPOT":
        job_script.append("ppafm-generate-ljff -i LOCPOT.xsf -F xsf -f npy")
    else:
        job_script.append("ppafm-generate-ljff -i in.xyz -F xyz -f npy")
    
    job_script.append("ppafm-relaxed-scan --pos -f npy")
    job_script.append("ppafm-plot-results --df --cbar -f npy")
        
    sub_script = [
        "now=$(date +%Y%m%d-%H%M%S)",
        "JOB_NAME=`scck job user`-$now",
        "sbatch \\",
        "    --job-name=\"$JOB_NAME\" \\",
        "    job.sh"
    ]
    
    return sub_script, job_script

run_options = {
    "empty": job_empty_template,
    "vasp": job_vasp_template,
    "ppafm": job_ppafm_template,
    "lammps": job_lammps_template,
}