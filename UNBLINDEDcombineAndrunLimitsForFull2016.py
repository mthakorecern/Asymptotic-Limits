import os
import shutil
import subprocess
import json
import numpy as np
import matplotlib.pyplot as plt

# Define parameters
years = ["2016", "2016APV"]
channels = ["tautau","leptau","inclusive"]
mass_points = ["1000", "1200", "1400", "1600", "1800", "2000", "2500", "3000", "3500", "4000", "4500"]
#mass_points = ["1200"]
postfix = "unblinded_Oct1_2025_preCWR"
output_dir = os.getcwd()
run2_dir = os.path.join(output_dir, f"Full2016_{postfix}")
combined_cards_dir = os.path.join(run2_dir, "combined_cards_2016")
workspaces_dir = os.path.join(run2_dir, "workspaces_2016")
combine_output_dir = os.path.join(run2_dir, "combine_output_2016")
logs_dir = os.path.join(run2_dir, "logs_2016")
limits_dir = os.path.join(run2_dir, "limits_2016")

# Create necessary directories
os.makedirs(combined_cards_dir, exist_ok=True)
os.makedirs(workspaces_dir, exist_ok=True)
os.makedirs(combine_output_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(limits_dir, exist_ok=True)

# Increase stack size for combine tool
subprocess.run("ulimit -s unlimited", shell=True, check=True)

for mass in mass_points:
    print(f"\n\n Processing mass point {mass}")
    combined_files = []

    # Process each channel separately
    for channel in channels:
    #for channel in channels + ["inclusive"]:
        channel_files = []
        channel_output_dir = os.path.join(combine_output_dir, channel)
        os.makedirs(channel_output_dir, exist_ok=True)

        # Collect datacards for 2016 and 2016APV
        for year in years:
            if channel == "inclusive":
                original_path = f"{year}_{postfix}/combined_cards_{year}/combined_{year}_{mass}.txt"
            else:
                original_path = f"{year}_{postfix}/combined_cards_{year}/{channel}/combined_{channel}_{year}_{mass}.txt"
            
            copied_path = os.path.join(output_dir, os.path.basename(original_path))
            
            if os.path.exists(original_path):
                os.system(f"cp {original_path} .")
                channel_files.append(os.path.basename(copied_path))
            else:
                print(f"Warning: Datacard not found for {original_path}")

        # Combine the datacards
        combined_file = os.path.join(output_dir, f"combined_2016_{channel}_{mass}.txt")
        if (channel != "inclusive"):
            combine_command = f"combineCards.py y2016APV=combined_{channel}_2016APV_{mass}.txt y2016=combined_{channel}_2016_{mass}.txt > {os.path.basename(combined_file)}"
        else:
            combine_command = f"combineCards.py y2016APV=combined_2016APV_{mass}.txt y2016=combined_2016_{mass}.txt > {os.path.basename(combined_file)}"
        print(f"CombineCards command: {combine_command}")

        try:
            subprocess.run(combine_command, shell=True, check=True)
            print(f"Created {combined_file}")

            # Run text2workspace
            workspace_file = os.path.join(output_dir, f"combined_2016_{channel}_{mass}.root")
            text2workspace_command = f"text2workspace.py {os.path.basename(combined_file)} -o {os.path.basename(workspace_file)} -m {mass}"
            print(f"T2W command: {text2workspace_command}")
            subprocess.run(text2workspace_command, shell=True, check=True)
            print(f"Created workspace {workspace_file}")

            # Run combine
            combine_result_file = os.path.join(output_dir, f"combine_result_2016_{channel}_{mass}.log")
            combine_command = f"combine -M AsymptoticLimits {os.path.basename(workspace_file)} -m {mass}"
            print(f"Combine command: {combine_command}")
            with open(combine_result_file, "w") as log_file:
                subprocess.run(combine_command, stdout=log_file, stderr=subprocess.STDOUT, shell=True, check=True)
            print(f"Combine results saved to {combine_result_file}")

            # Move files to final locations
            shutil.move(combined_file, os.path.join(combined_cards_dir, f"combined_2016_{channel}_{mass}.txt"))
            shutil.move(workspace_file, os.path.join(workspaces_dir, f"combined_2016_{channel}_{mass}.root"))
            subprocess.run(f"mv higgsCombineTest.AsymptoticLimits.mH*.root {channel_output_dir}/.", shell=True, check=True)
            shutil.move(combine_result_file, os.path.join(logs_dir, f"combine_result_2016_{channel}_{mass}.log"))

        except subprocess.CalledProcessError as e:
            print(f"Error during processing for mass point {mass}, channel {channel}: {e}")

        finally:
            for file in channel_files:
                if os.path.exists(file):
                    os.remove(file)

# Collect limits and plot for each channel
def collect_and_plot_limits():
    for channel in channels:
    #for channel in channels + ["inclusive"]:
        limit_json = os.path.join(limits_dir, f"limits_{channel}.json")
        channel_output_dir = os.path.join(combine_output_dir, channel)
        collect_command = f"combineTool.py -M CollectLimits {channel_output_dir}/higgsCombineTest.AsymptoticLimits.mH*.root -o {limit_json}"
        print(f"Collecting limits for {channel}: {collect_command}")
        subprocess.run(collect_command, shell=True, check=True)
        plot_limits(limit_json, limits_dir, channel)

###def plot_limits(json_file, output_dir, channel):
###    print(f"Plotting limits for {channel}...")
###    """Plot the limits using Matplotlib based on JSON data."""
###
###    # Load data from JSON file
###    with open(json_file) as f:
###        data = json.load(f)
###
###    # Extract data
###    masses = np.array([float(m) for m in data.keys()])
###    observed = np.array([data[m]["obs"] for m in data.keys()])
###    expected = np.array([data[m]["exp0"] for m in data.keys()])
###    exp1_up = np.array([data[m]["exp+1"] for m in data.keys()])
###    exp1_down = np.array([data[m]["exp-1"] for m in data.keys()])
###    exp2_up = np.array([data[m]["exp+2"] for m in data.keys()])
###    exp2_down = np.array([data[m]["exp-2"] for m in data.keys()])
###
###    # Create plot
###    plt.figure(figsize=(8, 6))
###    # Observed: solid black line with dots
###    plt.plot(masses, observed, 'o-', color='black', label='Observed', zorder=11)
###
###    # Expected: dashed black line
###    plt.plot(masses, expected, '--', color='black', label='Expected', zorder=10)
###
###    # 1σ and 2σ bands
###    plt.fill_between(masses, exp1_down, exp1_up, color='#FFDF7Fff', label='68% expected', zorder=3)
###    plt.fill_between(masses, exp2_down, exp2_up, color='#85D1FBff', label='95% expected')
###
###    # Labels and styles
###
###    plt.xlabel(r'$m_{X}$ (GeV)')
###    plt.ylabel(r'$95\%$ CL limit on $\sigma_{HH}$ (fb)')
###    plt.yscale('log')
###    plt.ylim(0.5, 1e4)
###    plt.legend(loc='upper right')
###    plt.legend(title=r"$X \rightarrow HH$ scaled to 1 fb")
###    plt.figtext(0.12, 0.92, "CMS Preliminary", ha="left", va="top", fontsize=12, fontweight='bold')
###    if channel == "tautau":
###        plt.figtext(0.14, 0.82, "Fully Hadronic", ha="left", va="top", fontsize=12, fontweight='bold')
###    elif channel == "leptau":
###        plt.figtext(0.14, 0.82, "Semi leptonic", ha="left", va="top", fontsize=12, fontweight='bold')
###    elif channel == "inclusive":
###        plt.figtext(0.14, 0.82, "Inclusive", ha="left", va="top", fontsize=12, fontweight='bold')
###
###    plt.figtext(0.88, 0.92, "36.67 $fb^{-1}$, 13 TeV", ha="right", va="top", fontsize=12)
###
###    # Save plot
###    plt.savefig(f"{output_dir}/limit_plot_{channel}_full2016.pdf")
###    plt.savefig(f"{output_dir}/limit_plot_{channel}_full2016.png")
###    plt.show()

#Plotting for comparison with Camilla
def plot_limits(json_file, output_dir, channel):
    print(f"Plotting limits for {channel}...")

    # Load data from JSON file
    with open(json_file) as f:
        data = json.load(f)

    # Extract data and convert fb to pb (1 fb = 1e-3 pb)
    masses = np.array([float(m) for m in data.keys()])
    observed = np.array([data[m]["obs"] * 1e-3 for m in data.keys()])
    expected = np.array([data[m]["exp0"] * 1e-3 for m in data.keys()])
    exp1_up = np.array([data[m]["exp+1"] * 1e-3 for m in data.keys()])
    exp1_down = np.array([data[m]["exp-1"] * 1e-3 for m in data.keys()])
    exp2_up = np.array([data[m]["exp+2"] * 1e-3 for m in data.keys()])
    exp2_down = np.array([data[m]["exp-2"] * 1e-3 for m in data.keys()])

    # Create plot
    plt.figure(figsize=(8, 6))
    plt.plot(masses, observed, 'o-', color='black', label='Observed', zorder=11)
    plt.plot(masses, expected, '--', color='black', label='Expected', zorder=10)
    plt.fill_between(masses, exp1_down, exp1_up, color='#FFDF7Fff', label='68% expected', zorder=3)
    plt.fill_between(masses, exp2_down, exp2_up, color='#85D1FBff', label='95% expected')

    # Labels and styles
    plt.xlabel(r'$m_{X}$ (GeV)')
    plt.ylabel(r'$95\%$ CL limit on $\sigma_{HH}$ (pb)')
    plt.yscale('log')
    plt.ylim(1e-3, 1e1)
    plt.tick_params(axis='y', which='both', direction='in', right=True)
    plt.tick_params(axis='x', which='both', direction='in', top=True)

    # Legend and text
    plt.legend(loc='upper right')
    plt.legend(title=r"$X \rightarrow HH$")
    plt.figtext(0.12, 0.92, "CMS Preliminary", ha="left", va="top", fontsize=12, fontweight='bold')

    if channel == "tautau":
        plt.figtext(0.14, 0.82, "Fully Hadronic", ha="left", va="top", fontsize=12, fontweight='bold')
    elif channel == "leptau":
        plt.figtext(0.14, 0.82, "Semi Leptonic", ha="left", va="top", fontsize=12, fontweight='bold')
    elif channel == "inclusive":
        plt.figtext(0.14, 0.82, "Inclusive", ha="left", va="top", fontsize=12, fontweight='bold')

    plt.figtext(0.88, 0.92, "36.67 $fb^{-1}$, 13 TeV", ha="right", va="top", fontsize=12)

    # Save plot
    plt.savefig(f"{output_dir}/limit_plot_{channel}_Camilla_full2016.pdf")
    plt.savefig(f"{output_dir}/limit_plot_{channel}_Camilla_full2016.png")
    plt.show()


try:
    collect_and_plot_limits()
except subprocess.CalledProcessError as e:
    print(f"Error during limit collection or plotting: {e}")
