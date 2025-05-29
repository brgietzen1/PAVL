import os
import subprocess

AVL_EXECUTABLE_PATH = "C:/Users/brgietzen/Documents/AVL/avl335/avl.exe"

def write_avl_command_file(jobname: str, results_dir: str) -> str:
    """
    Creates a command script for AVL to load geometry, mass, run case,
    and write out force and stability files.

    Returns:
        cmd_file (str): Path to the command script.
    """
    avl_file = os.path.join(results_dir, f"{jobname}.avl")
    run_file = os.path.join(results_dir, f"{jobname}.run")
    mass_file = os.path.join(results_dir, f"{jobname}.mass")
    force_file = os.path.join(results_dir, f"{jobname}_forces.txt")
    st_file = os.path.join(results_dir, f"{jobname}_stability.txt")
    cmd_file = os.path.join(results_dir, f"{jobname}_avl_commands.txt")

    with open(cmd_file, "w") as f:
        f.write(f"load {avl_file}\n")
        f.write(f"case {run_file}\n")
        f.write(f"mass {mass_file}\n")
        f.write("mset 0\n")
        f.write("oper\n")
        f.write("x\n")
        f.write("w\n")
        f.write(f"{force_file}\n")
        f.write("st\n")
        f.write(f"{st_file}\n")
        f.write("\n")
        f.write("quit\n")

    return cmd_file

def run_avl(jobname: str, results_dir: str, avl_exe_path: str = AVL_EXECUTABLE_PATH) -> None:
    """
    Executes AVL using the generated command file and captures output into a merged `.sim` result file.

    Parameters:
        jobname (str): Name of the job.
        results_dir (str): Directory where all result files are located.
        avl_exe_path (str): Path to the AVL executable.
    """
    cmd_file = write_avl_command_file(jobname, results_dir)
    sim_file = os.path.join(results_dir, f"{jobname}.sim")
    force_file = os.path.join(results_dir, f"{jobname}_forces.txt")
    st_file = os.path.join(results_dir, f"{jobname}_stability.txt")

    try:
        result = subprocess.run(
            [avl_exe_path],
            stdin=open(cmd_file, 'r'),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        force_data = ""
        st_data = ""

        if os.path.exists(force_file):
            with open(force_file, "r") as f:
                force_data = f.read()

        if os.path.exists(st_file):
            with open(st_file, "r") as f:
                lines = f.readlines()
                
                start_idx = 0
                for i, line in enumerate(lines):
                    if "Stability-axis derivatives" in line:
                        start_idx = i
                        break
                st_data = "".join(lines[start_idx:])

        with open(sim_file, "w") as f:
            f.write(force_data)
            f.write("\n" * 5)
            f.write(st_data)
            

        for file_path in [cmd_file, force_file, st_file]:
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Warning: Could not delete {file_path}: {e}")

        print(f"AVL simulation completed. Merged output saved to: {sim_file}")

    except Exception as e:
        print(f"[ERROR] Failed to run AVL: {e}")
