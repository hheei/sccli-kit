import os
import sys
import multiprocessing as mp
import subprocess
from pathlib import Path

from ..const import cmdlen

def _count_files_in_dir(path: Path):
    try:
        du_result = subprocess.run(f'lfs find {path} -type f | tee >(wc -l >&2) | xargs stat -c %b | awk "{{s+=\\$1}} END {{print s*512/1024}}"', text=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.split()[0]
    except subprocess.CalledProcessError:
        file_count = -1
        total_size = -1
    else:
        file_count, total_size = du_result.split()
        file_count = int(file_count)
        total_size = int(total_size)
    
    print("x", end="")
    
    return path, file_count, total_size

def _fmt_size(size):
    if size == -1:
        return "N/A"
    elif size < 1024:
        return f"{size:.2f}KB"
    elif size < 1024 * 1024:
        return f"{size / 1024:.2f}MB"
    else:
        return f"{size / 1024 / 1024:.2f}GB"

def run_dirstat():
    print(" " + " DIRSTAT ".center(cmdlen, "="))    
    blacklist = ("Library",)
    dirs = [d for d in Path.home().glob("*") if d.is_dir() and d.name not in blacklist]
    dirs = list(filter(lambda x: not x.name.startswith("."), dirs))

    results = []
    print(" " + "." * len(dirs), end="\r ")
    with mp.Pool() as pool:
        results = pool.map(_count_files_in_dir, dirs)
    print()
    
    results = sorted(results, key=lambda x: x[2], reverse=True)
    
    count_max_len = max(len(str(result[1])) for result in results) + 2
    size_max_len = max(len(str(result[2])) for result in results) + 2
    dir_max_len = max(max(len(str(result[0]).replace(str(Path.home()), "~")) for result in results) + 1, cmdlen - count_max_len - size_max_len)
    print(" " + "DIR".center(dir_max_len) + "COUNT".center(count_max_len) + "SIZE".center(size_max_len))
    print(" " + "-" * (dir_max_len + count_max_len + size_max_len))
    for dir_name, count, size in results:
        print(f" {str(dir_name).replace(str(Path.home()), '~'):<{dir_max_len}}{count:>{count_max_len}}{_fmt_size(size):>{size_max_len}}")
    print(" " + "-" * (dir_max_len + count_max_len + size_max_len))
    
    total_count = sum(filter(lambda x: x > 0, [result[1] for result in results]))
    total_size = sum(filter(lambda x: x > 0, [result[2] for result in results]))
    print(" " + f"{'Total'.ljust(dir_max_len)}{total_count:>{count_max_len}}{_fmt_size(total_size):>{size_max_len}}")
    sys.exit(0)