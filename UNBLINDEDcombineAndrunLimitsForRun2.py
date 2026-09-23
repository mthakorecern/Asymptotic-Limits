import os
import shutil
import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt

# Define parameters
years = ["2016", "2016APV", "2017", "2018"]
mass_points = ["1000", "1200", "1400", "1600", "1800", "2000", "2500", "3000", "3500", "4000", "4500"]
#mass_points = ["2000", "4000"]
postfix = "unblinded_Oct1_2025_preCWR"
output_dir = os.getcwd()
run2_dir = os.path.join(output_dir, f"Run2_{postfix}")
combined_cards_dir = os.path.join(run2_dir, "combined_cards_run2")
workspaces_dir = os.path.join(run2_dir, "workspaces_run2")
combine_output_dir = os.path.join(run2_dir, "combine_output_run2")
logs_dir = os.path.join(run2_dir, "logs_run2")
limits_dir = os.path.join(run2_dir, "limits")

# Create necessary directories
os.makedirs(combined_cards_dir, exist_ok=True)
os.makedirs(workspaces_dir, exist_ok=True)
os.makedirs(combine_output_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(limits_dir, exist_ok=True)

#Increasing Resources for full Run2-Combination
subprocess.run("ulimit -s unlimited", shell=True, check=True)

for mass in mass_points:
    print(f"\n\n\n\n\n\n\n Processing mass point {mass}")
    combined_files = []

    # Collect and copy datacards for all years
    for year in years:
        original_path = f"{year}_{postfix}/combined_cards_{year}/combined_{year}_{mass}.txt"
        copied_path = os.path.join(output_dir, os.path.basename(original_path))

        if os.path.exists(original_path):
            #shutil.copy(original_path, copied_path)
            print(f"\n\n")
            print (f"cp {original_path} {copied_path}")
            os.system(f"cp {original_path} .")
            combined_files.append(os.path.basename(copied_path))
        else:
            print(f"Warning: Datacard not found for {original_path}")

    # Combine the datacards
    combined_run2_file = os.path.join(output_dir, f"combined_run2_{mass}.txt")
    combine_command = f"combineCards.py y2016APV=combined_2016APV_{mass}.txt y2016=combined_2016_{mass}.txt y2017=combined_2017_{mass}.txt y2018=combined_2018_{mass}.txt > {os.path.basename(combined_run2_file)}"
    print (f"\n\n CombineCards command: {combine_command}")

    try:
        subprocess.run(combine_command, shell=True, check=True)
        print(f"Created {combined_run2_file}")

        # Run text2workspace
        workspace_file = os.path.join(output_dir, f"combined_run2_{mass}.root")
        print(f"\n\n")
        text2workspace_command = f"text2workspace.py {os.path.basename(combined_run2_file)} -o {os.path.basename(workspace_file)} -m {mass}"
        print ("T2W command : ",text2workspace_command)
        subprocess.run(text2workspace_command, shell=True, check=True)
        print(f"Created workspace {workspace_file}")

        # Run combine
        combine_result_file = os.path.join(output_dir, f"combine_result_{mass}.log")
        combine_command = f"combine -M AsymptoticLimits {os.path.basename(workspace_file)} -m {mass}"
        print(f"\n\n")
        print ("combine command: ",combine_command)
        with open(combine_result_file, "w") as log_file:
            subprocess.run(combine_command, stdout=log_file, stderr=subprocess.STDOUT, shell=True, check=True)
        print(f"Combine results saved to {combine_result_file}")

        # Move files to final locations
        shutil.move(combined_run2_file, os.path.join(combined_cards_dir, f"combined_run2_{mass}.txt"))
        shutil.move(workspace_file, os.path.join(workspaces_dir, f"combined_run2_{mass}.root"))
        #Move the combine output files to the appropriate location
        subprocess.run(f"mv higgsCombineTest.AsymptoticLimits.mH*.root {combine_output_dir}/.", shell=True, check=True)
        log_file_path = os.path.join(logs_dir, f"combine_result_{mass}.log")
        shutil.move(combine_result_file, log_file_path)

    except subprocess.CalledProcessError as e:
        print(f"Error during processing for mass point {mass}: {e}")

    finally:
        # Clean up copied files
        for file in combined_files:
            if os.path.exists(file):
                os.remove(file)

# Step 5: Collect limits and plot
def collect_limits():
    print("\n\n\n\n\n\n\n###-->Step 5: Collect limits and plot<--###")
    limit_json = os.path.join(limits_dir, "limits.json")
    collect_command = f"combineTool.py -M CollectLimits {combine_output_dir}/higgsCombineTest.AsymptoticLimits.mH*.root -o {limit_json}"
    print(f"\n\n")
    print ("Combine output collect command: ",collect_command)
    subprocess.run(collect_command, shell=True, check=True)
    return limit_json

def modify_limits_json(input_json, output_json):
    """Modify the limits JSON to account for branching ratio."""
    with open(input_json, 'r') as f:
        data = json.load(f)

    for key, value in data.items():
        for sub_key in value:
            value[sub_key] /= (2 * (0.53 * 0.06))  # Apply branching ratio correction

    with open(output_json, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)

def plot_limits(json_file, output_dir):
    """Plot the limits using Matplotlib based on JSON data."""

    # Load data from JSON file
    with open(json_file) as f:
        data = json.load(f)

    # Extract data
    masses = np.array([float(m) for m in data.keys()])
    observed = np.array([data[m]["obs"] for m in data.keys()])
    expected = np.array([data[m]["exp0"] for m in data.keys()])
    exp1_up = np.array([data[m]["exp+1"] for m in data.keys()])
    exp1_down = np.array([data[m]["exp-1"] for m in data.keys()])
    exp2_up = np.array([data[m]["exp+2"] for m in data.keys()])
    exp2_down = np.array([data[m]["exp-2"] for m in data.keys()])

    # Create plot
    plt.figure(figsize=(8, 6))
    # Observed: solid black line with dots
    plt.plot(masses, observed, 'o-', color='black', label='Observed', zorder=11)

    # Expected: dashed black line
    plt.plot(masses, expected, '--', color='black', label='Expected', zorder=10)

    # 1σ and 2σ bands
    plt.fill_between(masses, exp1_down, exp1_up, color='#FFDF7Fff', label='68% expected', zorder=3)
    plt.fill_between(masses, exp2_down, exp2_up, color='#85D1FBff', label='95% expected')

    # Labels and styles

    plt.xlabel(r'$m_{X}$ (GeV)')
    plt.ylabel(r'$95\%$ CL limit on $\sigma_{HH}$ (fb)')
    plt.yscale('log')
    plt.ylim(0.5, 1e4)
    plt.legend(loc='upper right')
    plt.legend(title=r"$X \rightarrow HH \rightarrow bb\tau\tau$ scaled to 1 fb")
    plt.figtext(0.12, 0.92, "CMS Preliminary", ha="left", va="top", fontsize=12, fontweight='bold')
    plt.figtext(0.88, 0.92, "138.12 $fb^{-1}$, 13 TeV", ha="right", va="top", fontsize=12)

    # Save plot
    plt.savefig(f"{output_dir}/limit_plot_run2.pdf")
    plt.savefig(f"{output_dir}/limit_plot_run2.png")
    plt.show()

try:
    limit_json = collect_limits()
    modified_limit_json = os.path.join(limits_dir, "limits_modified.json")
    modify_limits_json(limit_json, modified_limit_json)
    print ("I am plotting non-modified limits. Please be aware if this is required...")
    #plot_limits(modified_limit_json, limits_dir)
    plot_limits(limit_json, limits_dir)
except subprocess.CalledProcessError as e:
    print(f"Error during limit collection or plotting: {e}")
