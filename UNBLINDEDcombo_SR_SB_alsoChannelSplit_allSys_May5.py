import os
import subprocess
import shutil
import CombineHarvester.CombineTools.ch as ch
from ROOT import TFile
import argparse
import json
import ROOT
from CombineHarvester.CombineTools.plotting import *
import json
import matplotlib 
matplotlib.use("Agg") # issues with matplotlib on some login nodes 
import matplotlib.pyplot as plt
import numpy as np
import mplhep as hep
import glob


def find_channel(data_string):
    # Define a regex pattern to match the years/keywords even if they are part of a larger word
    pattern = r"(tautau|leptau)"
    match = re.search(pattern, data_string)
    # If there's a match, return it
    if match:
        return match.group(0)
    return None


def run_command(command):
    """Run a shell command."""
    subprocess.run(command, shell=True, check=True)


def create_directory(dir_name):
    """Create directory if it doesn't exist."""
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def prepare_parent_directory(parent_dir):
    """Delete parent directory if it exists, then recreate it."""
    if os.path.exists(parent_dir):
        shutil.rmtree(parent_dir)
    os.makedirs(parent_dir)


def modify_limits_json(input_json, output_json):
    """Modify the limits JSON to account for branching ratio."""
    with open(input_json, "r") as f:
        data = json.load(f)

    for key, value in data.items():
        for sub_key in value:
            value[sub_key] /= 2 * (0.53 * 0.06)  # Apply branching ratio correction

    with open(output_json, "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def plot_limits(json_file, output_dir, year, channel=None):
    """Plot the limits using Matplotlib based on JSON data."""

    # Load data from JSON file
    with open(json_file) as f:
        data = json.load(f)

    # Extract data
    masses = np.array([float(m) for m in data.keys()])
    # observed = np.array([data[m]["obs"] for m in data.keys()])
    expected = np.array([data[m]["exp0"] for m in data.keys()])
    exp1_up = np.array([data[m]["exp+1"] for m in data.keys()])
    exp1_down = np.array([data[m]["exp-1"] for m in data.keys()])
    exp2_up = np.array([data[m]["exp+2"] for m in data.keys()])
    exp2_down = np.array([data[m]["exp-2"] for m in data.keys()])

    # Create plot
    plt.figure(figsize=(8, 6))
    # # Observed: solid black line with dots
    # plt.plot(masses, observed, "o-", color="black", label="Observed", zorder=11)

    # Expected: dashed black line
    plt.plot(masses, expected, "o-", color="black", label="Expected", zorder=10)

    # 1σ and 2σ bands
    plt.fill_between(
        masses, exp1_down, exp1_up, color="#FFDF7Fff", label="68% expected", zorder=3
    )
    plt.fill_between(
        masses, exp2_down, exp2_up, color="#85D1FBff", label="95% expected"
    )

    # Labels and styles

    plt.xlabel(r"$m_{X}$ (GeV)")
    plt.ylabel(r"$95\%$ CL limit on $\sigma_{HH}$ (fb)")
    plt.yscale("log")
    plt.ylim(0.5, 1e4)
    plt.legend(loc="upper right")
    plt.legend(title=r"$X \rightarrow HH$ scaled to 1fb")
    plt.figtext(
        0.12,
        0.92,
        "CMS Preliminary",
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
    )
    if channel == "tt":
        plt.figtext(
            0.14,
            0.82,
            "Tau - Tau",
            ha="left",
            va="top",
            fontsize=12,
            fontweight="bold",
        )
    elif channel == "et":
        plt.figtext(
            0.14,
            0.82,
            "Electron - Tau",
            ha="left",
            va="top",
            fontsize=12,
            fontweight="bold",
        )
    elif channel == "mt":
        plt.figtext(
            0.14,
            0.82,
            "Muon - Tau",
            ha="left",
            va="top",
            fontsize=12,
            fontweight="bold",
        )
    elif channel == "lt":
        plt.figtext(
            0.14,
            0.82,
            "Semi-Leptonic",
            ha="left",
            va="top",
            fontsize=12,
            fontweight="bold",
        )
    plt.figtext(
        0.12,
        0.92,
        "CMS Preliminary",
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
    )
    plt.figtext(0.88, 0.92, f"({year}, 13.6 TeV)", ha="right", va="top", fontsize=12)

    # Save plot
    plt.savefig(f"{output_dir}/limit_plot_{year}.pdf")
    plt.savefig(f"{output_dir}/limit_plot_{year}.png")
    plt.show()


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run Combine Harvester with custom histogram path, year, and parent directory"
    )
    parser.add_argument(
        "--histogram_path",
        type=str,
        required=True,
        help="Path to the ROOT file containing histograms",
    )
    parser.add_argument(
        "--year",
        type=str, 
        required=True, 
        help="Year of the dataset (e.g., 2024)"
    )
    parser.add_argument(
        "--parent_dir",
        type=str,
        required=True,
        help="Parent directory for storing outputs",
    )
    parser.add_argument(
        "--addSystematics",
        action="store_true",
        help="Add lnN and shape systematic uncertainties to the datacards.",
    )

    parser.add_argument(
        "--noAutoMCStats",
        action="store_true",
        help="Disable autoMCStats. By default MC statistical uncertainties are included.",
    )
    args = parser.parse_args()

    aux_shapes_SR = args.histogram_path + "/" + "SR_bin_by_bin_rootfiles"
    aux_shapes_SB = args.histogram_path + "/" + "SB_bin_by_bin_rootfiles"
    year = args.year
    parent_dir = args.parent_dir

    # Directories for organizing outputs under the parent directory
    datacard_dir = os.path.join(parent_dir, f"datacards_{year}")
    combined_dir = os.path.join(parent_dir, f"combined_cards_{year}")
    workspace_dir = os.path.join(parent_dir, f"workspaces_{year}")
    output_dir = os.path.join(parent_dir, f"combine_output_{year}")
    limit_dir = os.path.join(parent_dir, f"limits_{year}")

    create_directory(datacard_dir)
    create_directory(combined_dir)
    create_directory(workspace_dir)
    create_directory(output_dir)
    create_directory(limit_dir)

    bin_edges = [750, 900, 1050, 1200, 1350, 1500, 1650, 1800, 1950, 2200, 2450, 5500]

    n_bins = len(bin_edges) - 1

    mass_bins = {}
    for bin in range(1, n_bins + 1):
        lower_edge = str(bin_edges[bin - 1])
        upper_edge = str(bin_edges[bin])
        mass_bins[f"{lower_edge}_{upper_edge}"] = (
            f"{year}_allHists_SignalRegion_1fb_varbin_mass_{lower_edge}_{upper_edge}.root"
        )

    mass_bins_sideband = {}
    for bin in range(1, n_bins + 1):
        lower_edge = str(bin_edges[bin - 1])
        upper_edge = str(bin_edges[bin])
        mass_bins_sideband[f"{lower_edge}_{upper_edge}"] = (
            f"{year}_allHists_SideBand_1fb_varbin_mass_{lower_edge}_{upper_edge}.root"
        )

    # Define the channels with mass ranges included in the category names

    # Generate separate datacards and output files for each mass range
    print(
        "\n\n\n\n\n###--> Step 1.0: Generate datacards for each mass point by mass range for Side Band Region <--###"
    )
    small_value = 1e-06  # Small placeholder value for empty bins
    signal_masses = [
        "1000",
        "1200",
        "1400",
        "1600",
        "1800",
        "2000",
        "2500",
        "3000",
        "3500",
        "4000",
        "4500",
    ]
    for signal_mass in signal_masses:
        print("\n\n\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("Processing the signal mass point = ", signal_mass)
        for mass_range, root_file in mass_bins_sideband.items():
            cb = ch.CombineHarvester()
            print("\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(f"Processing mass range: {mass_range} using file {root_file}")

            cats = [
                (1, f"tautau_{year}_{mass_range}_SB"),
                (2, f"leptau_{year}_{mass_range}_SB"),
            ]

            cb.AddObservations(["*"], ["xhhbbtt"], [year], [""], cats)

            bkg_procs = ["top", "others"]
            sig_procs = ["radion"]
            # masses = ['1000', '1200', '1400', '1600', '1800', '2000', '2500', '3000', '3500', '4000', '4500']

            masses = [signal_mass]

            cb.AddProcesses(["*"], ["xhhbbtt"], [year], [""], bkg_procs, cats, False)
            cb.AddProcesses(masses, ["xhhbbtt"], [year], [""], sig_procs, cats, True)
            # lumi_uncorr_uncertainties = {
            #     "2016": 1.010,  # 1.0% uncertainty for 2016
            #     "2016APV": 1.010,
            #     "2017": 1.020,  # Example: 2.0% uncertainty for 2017
            #     "2018": 1.015,  # 1.5% uncertainty for 2018
            # }
            # lumi_partial_uncertainties = {
            #     "2017": 1.006,  # Example: 2.0% uncertainty for 2017
            #     "2018": 1.002,  # 1.5% uncertainty for 2018
            # }
            # lumi_corr_uncertainties = {
            #     "2016": 1.006,  # 1.0% uncertainty for 2016
            #     "2016APV": 1.006,
            #     "2017": 1.009,  # Example: 2.0% uncertainty for 2017
            #     "2018": 1.020,  # 1.5% uncertainty for 2018
            # }

            # l1prefiring_uncertainties = {
            #     "2016": 1.01,
            #     "2016APV": 1.01,
            #     "2017": 1.01,
            #     "2018": 1.005,  # For 2018 it is usually not applicable or negligible
            # }

            # jes_year_unc = {
            #     "2016": "2016",
            #     "2016APV": "2016",
            #     "2017": "2017",
            #     "2018": "2018",  # For 2018 it is usually not applicable or negligible
            # }

            # lnN_systematics = [
            #     (
            #         "lumi%s" % (year),
            #         "lnN",
            #         {
            #             "others": lumi_uncorr_uncertainties[year],
            #             "radion": lumi_uncorr_uncertainties[year],
            #         },
            #     ),
            #     (
            #         "lumi_1718",
            #         "lnN",
            #         {
            #             "others": lumi_partial_uncertainties[year],
            #             "radion": lumi_partial_uncertainties[year],
            #         },
            #     )
            #     if args.year == "2017" or args.year == "2018"
            #     else None,  # Luminosity for 2017-2018
            #     (
            #         "lumi_161718",
            #         "lnN",
            #         {
            #             "others": lumi_corr_uncertainties[year],
            #             "radion": lumi_corr_uncertainties[year],
            #         },
            #     ),
            #     ("Unclust", "lnN", {"others": 1.01, "radion": 1.01}),
            #     ("tes", "lnN", {"others": 1.10}),
            #     # ("jer", "lnN",{"others": 1.05,"radion":1.10}),
            #     ("jer", "lnN", {"others": 1.05}),
            #     ("pileupcorrWeight", "lnN", {"others": 1.15}),
            #     ("jesAbsolute", "lnN", {"others": 1.05}),
            #     ("jesAbsolute_%s" % (jes_year_unc[year]), "lnN", {"others": 1.05}),
            #     ("jesBBEC1", "lnN", {"others": 1.05}),
            #     (
            #         "jesBBEC1_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.02, "radion": 1.02},
            #     ),
            #     ("jesEC2", "lnN", {"others": 1.02, "radion": 1.02}),
            #     (
            #         "jesEC2_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.02, "radion": 1.02},
            #     ),
            #     ("jesFlavorQCD", "lnN", {"others": 1.02, "radion": 1.02}),
            #     ("jesHF", "lnN", {"others": 1.02, "radion": 1.02}),
            #     (
            #         "jesHF_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.02, "radion": 1.02},
            #     ),
            #     ("jesRelativeBal", "lnN", {"others": 1.05, "radion": 1.05}),
            #     (
            #         "jesRelativeSample_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.05},
            #     ),
            #     # ("L1PreFiringWeight_Nom", "lnN",{"others": 1.01,"radion":1.01}),
            #     (
            #         "L1PreFiringWeight",
            #         "lnN",
            #         {
            #             "others": l1prefiring_uncertainties[year],
            #             "radion": l1prefiring_uncertainties[year],
            #         },
            #     ),
            #     (
            #         f"boostedDeepTauid",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SB": {
            #                 "others": 1.10,
            #                 "radion": 1.10,
            #             },
            #             f"tautau_{year}_{mass_range}_SB": {
            #                 "others": 1.20,
            #                 "radion": 1.20,
            #             },  # Ensure this is handled gracefully
            #         },
            #     ),
            #     # The above needs to be updated later
            #     (
            #         "metsfWeight",
            #         "lnN",
            #         {"others": 1.012, "radion": 1.012},
            #     ),  # Fixed format
            #     ("hbblooseWeight", "lnN", {"radion": 1.05}),  # Signal-specific weight
            #     (
            #         "eleidWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SB": {
            #                 "others": 1.004,
            #                 "radion": 1.004,
            #             },
            #             f"tautau_{year}_{mass_range}_SB": {},  # Ensure this is handled gracefully
            #         },
            #     ),
            #     (
            #         "elerecoWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SB": {
            #                 "others": 1.004,
            #                 "radion": 1.004,
            #             },
            #             f"tautau_{year}_{mass_range}_SB": {},  # Ensure this is handled gracefully
            #         },
            #     ),
            #     (
            #         "muonidWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SB": {
            #                 "others": 1.01,
            #                 "radion": 1.01,
            #             },
            #             f"tautau_{year}_{mass_range}_SB": {},
            #         },
            #     ),
            #     (
            #         "muonisoWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SB": {
            #                 "others": 1.001,
            #                 "radion": 1.001,
            #             },
            #             f"tautau_{year}_{mass_range}_SB": {},
            #         },
            #     ),
            # ]

            # lnN_systematics = [entry for entry in lnN_systematics if entry is not None]

            # shape_systematics = [
            #     # JER
            #     # ("tes", "shape", {"*": ["others", "radion"]}),
            #     ("tes", "shape", {"*": ["radion"]}),
            #     # ("L1PreFiringWeight_Nom","shape",{"*": ["others", "radion"]}),
            #     ("jer", "shape", {"*": ["radion"]}),  # Jet energy resolution
            #     # ("jer", "shape", {"*": ["top", "others"]}),
            #     # JES
            #     ("jesAbsolute", "shape", {"*": ["radion"]}),
            #     ("jesAbsolute_%s" % (jes_year_unc[year]), "shape", {"*": ["radion"]}),
            #     ("jesBBEC1", "shape", {"*": ["radion"]}),
            #     (
            #         "jesRelativeSample_%s" % (jes_year_unc[year]),
            #         "shape",
            #         {"*": ["radion"]},
            #     ),
            #     ("btagmediumWeightbc", "shape", {"*": ["others", "radion"]}),
            #     ("btagmediumWeightbc%s" % (year), "shape", {"*": ["others", "radion"]}),
            #     ("btagmediumWeightlight", "shape", {"*": ["others", "radion"]}),
            #     (
            #         "btagmediumWeightlight%s" % (year),
            #         "shape",
            #         {"*": ["others", "radion"]},
            #     ),
            #     # Theory
            #     ("ewkWDeborahsWeight", "shape", {"*": ["others"]}),
            #     ("ewkZDeborahsWeight", "shape", {"*": ["others"]}),
            #     ("qcdWWeightRen", "shape", {"*": ["others"]}),
            #     ("qcdWWeightFac", "shape", {"*": ["others"]}),
            #     ("qcdZTo2LWeightRen", "shape", {"*": ["others"]}),
            #     ("qcdZTo2LWeightFac", "shape", {"*": ["others"]}),
            #     # ("topptWeight", "shape", {"*": ["top"]}),
            #     ("pdf", "shape", {"*": ["others", "radion"]}),
            #     ("qcdscalefacto", "shape", {"*": ["others", "radion"]}),
            #     ("qcdscalerenorm", "shape", {"*": ["others", "radion"]}),
            #     # Other Standard Weights
            #     ("pileupcorrWeight", "shape", {"*": ["radion"]}),
            #     ("hpstauidWeight", "shape", {"*": ["others", "radion"]}),
            # ]

            # Add log-normal systematics
            # for sys_name, sys_type, sys_vals in lnN_systematics:
            #    for proc, val in sys_vals.items():
            #        cb.cp().process([proc] if proc != "*" else bkg_procs + sig_procs).AddSyst(
            #            cb, sys_name, sys_type, ch.SystMap()(val)
            #        )
            # Add log-normal systematics
            if args.addSystematics:
                print("\n>>> Adding systematic uncertainties to SB datacards")
                for sys_name, sys_type, sys_vals in lnN_systematics:
                    if (
                        sys_vals is None
                    ):  # Skip None values (e.g., lumi_1718 when year is not 2017 or 2018)
                        continue
                    for channel, processes in sys_vals.items():
                        # If the systematic is channel-specific
                        if isinstance(processes, dict):  # For nested dictionaries
                            for proc, val in processes.items():
                                cb.cp().bin([channel]).process([proc]).AddSyst(
                                    cb, sys_name, sys_type, ch.SystMap()(val)
                                )
                        else:
                            # General case for non-channel-specific systematics
                            for proc, val in sys_vals.items():
                                cb.cp().process(
                                    [proc] if proc != "*" else bkg_procs + sig_procs
                                ).AddSyst(cb, sys_name, sys_type, ch.SystMap()(val))
                # Add shape systematics
                for sys_name, sys_type, sys_categories in shape_systematics:
                    for cat, procs in sys_categories.items():
                        cb.cp().bin(
                            [cat]
                            if cat != "*"
                            else [
                                f"tautau_{year}_{mass_range}_SB",
                                f"leptau_{year}_{mass_range}_SB",
                            ]
                        ).process(procs).AddSyst(cb, sys_name, sys_type, ch.SystMap()(1.0))
            else:
                print("\n>>> Systematic uncertainties disabled for SB")
            

            # Extract shapes from the specified root file
            cb.cp().backgrounds().ExtractShapes(
                os.path.join(aux_shapes_SB, root_file),
                "$BIN/$PROCESS",
                "$BIN/$PROCESS_$SYSTEMATIC",
            )
            cb.cp().signals().ExtractShapes(
                os.path.join(aux_shapes_SB, root_file),
                "$BIN/$PROCESS$MASS",
                "$BIN/$PROCESS$MASS_$SYSTEMATIC",
            )

            # Create an output root file for the current mass range
            output = ROOT.TFile(
                f"{datacard_dir}/YEAR_{year}_RANGE_{mass_range}_SideBand_MASSPOINT_{signal_mass}_1fb_varbin.root",
                "RECREATE",
            )

            # Loop over bins in the current mass range
            print("All the bins = ", cb.bin_set())
            for b in cb.bin_set():
                print("Processing bin (BEFORE IF CONDITION):", b)
                if mass_range in b:
                    print("Processing bin:", b)
                    # Check if bin is empty by summing contributions from all processes
                    total_yield = 0

                    # Loop over all bkg processes in the bin and add their rates to total_yield
                    # for proc in cb.cp().bin([b]).process_set(): (Thi is for all processes)
                    for proc in cb.cp().bin([b]).backgrounds().process_set():
                        rate = cb.cp().bin([b]).process([proc]).GetRate()
                        # if (mass_range=="4500_4750"):
                        print(
                            "For the process..",
                            proc,
                            "...in the bin...",
                            "...rate..",
                            rate,
                        )
                        total_yield += rate
                    if total_yield == 0:
                        # Set a small yield value for each process in the empty bin
                        for proc in cb.cp().bin([b]).backgrounds().process_set():
                            print("Filling the small value for...", proc)
                            cb.cp().bin([b]).process([proc]).ForEachProc(
                                lambda p: p.set_rate(small_value)
                            )
                            print(
                                "After filling the rate = ",
                                cb.cp().bin([b]).process([proc]).GetRate(),
                            )

                    for m in masses:
                        datacard_filename = f"{datacard_dir}/{b}_S0_{m}.txt"
                        print(f">> Writing datacard for bin: {b} and Radionmass: {m}")
                        cb.cp().bin([b]).mass([m, "*"]).WriteDatacard(
                            datacard_filename, output
                        )

                        # Add autoMCStats and rate parameter constraints
                        with open(datacard_filename, "a") as out:
                            # out.write(f"rate_top_{find_channel(b)}_{year}_{mass_range} rateParam {b} top 1.0 [0.5,1.5]\n")
                            # out.write(f"SR_rate_top_{find_channel(b)}_{year}_{mass_range} rateParam {b} top 1.0 [0.5,1.5]\n")
                            # out.write(f"rate_top_{find_channel(b)}_{year} rateParam {b} top 1.0 [0.5,1.5]\n")
                            out.write(
                                f"rate_top_{find_channel(b)}_{year}_{mass_range} rateParam {b} top 1.0 [0.01,10]\n"
                            )
                            if not args.noAutoMCStats:
                                out.write(f"{b} autoMCStats 50 0 1\n")

            output.Close()

    # Generate separate datacards and output files for each mass range
    print(
        "\n\n\n\n\n###--> Step 1.5: Generate datacards for each mass point by mass range for Signal Region <--###"
    )
    small_value = 1e-06  # Small placeholder value for empty bins
    signal_masses = [
        "1000",
        "1200",
        "1400",
        "1600",
        "1800",
        "2000",
        "2500",
        "3000",
        "3500",
        "4000",
        "4500",
    ]
    # signal_masses = ['1400', '1600','2000']
    # signal_masses = ['2500', '3000', '3500', '4000', '4500']
    # revert ganesh
    # signal_masses = ['1000', '1200', '1400','1600', '1800', '2000', '2500']
    for signal_mass in signal_masses:
        print("\n\n\n\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print("Processing the signal mass point = ", signal_mass)
        for mass_range, root_file in mass_bins.items():
            cb = ch.CombineHarvester()
            print("\n\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(f"Processing mass range: {mass_range} using file {root_file}")

            cats = [
                (1, f"tautau_{year}_{mass_range}_SR"),
                (2, f"leptau_{year}_{mass_range}_SR"),
            ]
            # (3, f'CHANNEL_mt_YEAR_{year}_RANGE_{mass_range}_SR')]

            cb.AddObservations(["*"], ["xhhbbtt"], [year], [""], cats)

            bkg_procs = ["top", "others"]
            sig_procs = ["radion"]
            # masses = ['1000', '1200', '1400', '1600', '1800', '2000', '2500', '3000', '3500', '4000', '4500']

            masses = [signal_mass]

            cb.AddProcesses(["*"], ["xhhbbtt"], [year], [""], bkg_procs, cats, False)
            cb.AddProcesses(masses, ["xhhbbtt"], [year], [""], sig_procs, cats, True)

            # lumi_uncorr_uncertainties = {
            #     "2016": 1.010,  # 1.0% uncertainty for 2016
            #     "2016APV": 1.010,
            #     "2017": 1.020,  # Example: 2.0% uncertainty for 2017
            #     "2018": 1.015,  # 1.5% uncertainty for 2018
            # }
            # lumi_partial_uncertainties = {
            #     "2017": 1.006,  # Example: 2.0% uncertainty for 2017
            #     "2018": 1.002,  # 1.5% uncertainty for 2018
            # }
            # lumi_corr_uncertainties = {
            #     "2016": 1.006,  # 1.0% uncertainty for 2016
            #     "2016APV": 1.006,
            #     "2017": 1.009,  # Example: 2.0% uncertainty for 2017
            #     "2018": 1.020,  # 1.5% uncertainty for 2018
            # }
            # l1prefiring_uncertainties = {
            #     "2016": 1.01,
            #     "2016APV": 1.01,
            #     "2017": 1.01,
            #     "2018": 1.005,  # For 2018 it is usually not applicable or negligible
            # }
            # jes_year_unc = {
            #     "2016": "2016",
            #     "2016APV": "2016",
            #     "2017": "2017",
            #     "2018": "2018",  # For 2018 it is usually not applicable or negligible
            # }

            # lnN_systematics = [
            #     (
            #         "lumi%s" % (year),
            #         "lnN",
            #         {
            #             "others": lumi_uncorr_uncertainties[year],
            #             "radion": lumi_uncorr_uncertainties[year],
            #         },
            #     ),
            #     (
            #         "lumi_1718",
            #         "lnN",
            #         {
            #             "others": lumi_partial_uncertainties[year],
            #             "radion": lumi_partial_uncertainties[year],
            #         },
            #     )
            #     if args.year == "2017" or args.year == "2018"
            #     else None,  # Luminosity for 2017-2018
            #     (
            #         "lumi_161718",
            #         "lnN",
            #         {
            #             "others": lumi_corr_uncertainties[year],
            #             "radion": lumi_corr_uncertainties[year],
            #         },
            #     ),
            #     ("Unclust", "lnN", {"others": 1.01, "radion": 1.01}),
            #     ("tes", "lnN", {"others": 1.10}),
            #     # ("jer", "lnN",{"others": 1.05,"radion":1.10}),
            #     ("jer", "lnN", {"others": 1.05}),
            #     ("pileupcorrWeight", "lnN", {"others": 1.15}),
            #     ("jesAbsolute", "lnN", {"others": 1.05}),
            #     ("jesAbsolute_%s" % (jes_year_unc[year]), "lnN", {"others": 1.05}),
            #     ("jesBBEC1", "lnN", {"others": 1.05}),
            #     (
            #         "jesBBEC1_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.02, "radion": 1.02},
            #     ),
            #     ("jesEC2", "lnN", {"others": 1.02, "radion": 1.02}),
            #     (
            #         "jesEC2_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.02, "radion": 1.02},
            #     ),
            #     ("jesFlavorQCD", "lnN", {"others": 1.02, "radion": 1.02}),
            #     ("jesHF", "lnN", {"others": 1.02, "radion": 1.02}),
            #     (
            #         "jesHF_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.02, "radion": 1.02},
            #     ),
            #     ("jesRelativeBal", "lnN", {"others": 1.05, "radion": 1.05}),
            #     (
            #         "jesRelativeSample_%s" % (jes_year_unc[year]),
            #         "lnN",
            #         {"others": 1.05},
            #     ),
            #     (
            #         "L1PreFiringWeight",
            #         "lnN",
            #         {
            #             "others": l1prefiring_uncertainties[year],
            #             "radion": l1prefiring_uncertainties[year],
            #         },
            #     ),
            #     (
            #         f"boostedDeepTauid",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SR": {
            #                 "others": 1.10,
            #                 "radion": 1.10,
            #             },
            #             f"tautau_{year}_{mass_range}_SR": {
            #                 "others": 1.20,
            #                 "radion": 1.20,
            #             },  # Ensure this is handled gracefully
            #         },
            #     ),
            #     (
            #         "metsfWeight",
            #         "lnN",
            #         {"others": 1.012, "radion": 1.012},
            #     ),  # Fixed format
            #     ("hbblooseWeight", "lnN", {"radion": 1.05}),  # Signal-specific weight
            #     (
            #         "eleidWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SR": {
            #                 "others": 1.004,
            #                 "radion": 1.004,
            #             },
            #             f"tautau_{year}_{mass_range}_SR": {},  # Ensure this is handled gracefully
            #         },
            #     ),
            #     (
            #         "elerecoWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SR": {
            #                 "others": 1.004,
            #                 "radion": 1.004,
            #             },
            #             f"tautau_{year}_{mass_range}_SR": {},  # Ensure this is handled gracefully
            #         },
            #     ),
            #     (
            #         "muonidWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SR": {
            #                 "others": 1.01,
            #                 "radion": 1.01,
            #             },
            #             f"tautau_{year}_{mass_range}_SR": {},
            #         },
            #     ),
            #     (
            #         "muonisoWeight",
            #         "lnN",
            #         {
            #             f"leptau_{year}_{mass_range}_SR": {
            #                 "others": 1.001,
            #                 "radion": 1.001,
            #             },
            #             f"tautau_{year}_{mass_range}_SR": {},
            #         },
            #     ),
            # ]

            # lnN_systematics = [entry for entry in lnN_systematics if entry is not None]

            # shape_systematics = [
            #     ("tes", "shape", {"*": ["radion"]}),
            #     ("jer", "shape", {"*": ["radion"]}),  # Jet energy resolution
            #     # ("jer", "shape", {"*": ["top", "others"]}),
            #     # JES
            #     ("jesAbsolute", "shape", {"*": ["radion"]}),
            #     ("jesAbsolute_%s" % (jes_year_unc[year]), "shape", {"*": ["radion"]}),
            #     ("jesBBEC1", "shape", {"*": ["radion"]}),
            #     (
            #         "jesRelativeSample_%s" % (jes_year_unc[year]),
            #         "shape",
            #         {"*": ["radion"]},
            #     ),
            #     ("btagmediumWeightbc", "shape", {"*": ["others", "radion"]}),
            #     ("btagmediumWeightbc%s" % (year), "shape", {"*": ["others", "radion"]}),
            #     ("btagmediumWeightlight", "shape", {"*": ["others", "radion"]}),
            #     (
            #         "btagmediumWeightlight%s" % (year),
            #         "shape",
            #         {"*": ["others", "radion"]},
            #     ),
            #     # Theory
            #     ("ewkWDeborahsWeight", "shape", {"*": ["others"]}),
            #     ("ewkZDeborahsWeight", "shape", {"*": ["others"]}),
            #     ("qcdWWeightRen", "shape", {"*": ["others"]}),
            #     ("qcdWWeightFac", "shape", {"*": ["others"]}),
            #     ("qcdZTo2LWeightRen", "shape", {"*": ["others"]}),
            #     ("qcdZTo2LWeightFac", "shape", {"*": ["others"]}),
            #     # ("topptWeight", "shape", {"*": ["top"]}),
            #     ("pdf", "shape", {"*": ["others", "radion"]}),
            #     ("qcdscalefacto", "shape", {"*": ["others", "radion"]}),
            #     ("qcdscalerenorm", "shape", {"*": ["others", "radion"]}),
            #     # Other Standard Weights
            #     ("pileupcorrWeight", "shape", {"*": ["radion"]}),
            #     ("hpstauidWeight", "shape", {"*": ["others", "radion"]}),
            # ]

            if args.addSystematics:
                print("\n>>> Adding systematic uncertainties to SR datacards")

                for sys_name, sys_type, sys_vals in lnN_systematics:
                    if (
                        sys_vals is None
                    ):  # Skip None values (e.g., lumi_1718 when year is not 2017 or 2018)
                        continue
                    for channel, processes in sys_vals.items():
                        # If the systematic is channel-specific
                        if isinstance(processes, dict):  # For nested dictionaries
                            for proc, val in processes.items():
                                cb.cp().bin([channel]).process([proc]).AddSyst(
                                    cb, sys_name, sys_type, ch.SystMap()(val)
                                )
                        else:
                            # General case for non-channel-specific systematics
                            for proc, val in sys_vals.items():
                                cb.cp().process(
                                    [proc] if proc != "*" else bkg_procs + sig_procs
                                ).AddSyst(cb, sys_name, sys_type, ch.SystMap()(val))

                # Add shape systematics
                for sys_name, sys_type, sys_categories in shape_systematics:
                    for cat, procs in sys_categories.items():
                        cb.cp().bin(
                            [cat]
                            if cat != "*"
                            else [
                                f"tautau_{year}_{mass_range}_SR",
                                f"leptau_{year}_{mass_range}_SR",
                            ]
                        ).process(procs).AddSyst(cb, sys_name, sys_type, ch.SystMap()(1.0))
            else:
                print("\n>>> Systematic uncertainties disabled for SR")

            # Extract shapes from the specified root file
            cb.cp().backgrounds().ExtractShapes(
                os.path.join(aux_shapes_SR, root_file),
                "$BIN/$PROCESS",
                "$BIN/$PROCESS_$SYSTEMATIC",
            )
            cb.cp().signals().ExtractShapes(
                os.path.join(aux_shapes_SR, root_file),
                "$BIN/$PROCESS$MASS",
                "$BIN/$PROCESS$MASS_$SYSTEMATIC",
            )

            # Create an output root file for the current mass range
            output = ROOT.TFile(
                f"{datacard_dir}/YEAR_{year}_RANGE_{mass_range}_SignalRegion_MASSPOINT_{signal_mass}_1fb_varbin.root",
                "RECREATE",
            )

            # Loop over bins in the current mass range
            print("All the bins = ", cb.bin_set())
            for b in cb.bin_set():
                print("Processing bin (BEFORE IF CONDITION):", b)
                if mass_range in b:
                    print("Processing bin:", b)
                    # Check if bin is empty by summing contributions from all processes
                    total_yield = 0

                    # Loop over all bkg processes in the bin and add their rates to total_yield
                    # for proc in cb.cp().bin([b]).process_set(): (Thi is for all processes)
                    for proc in cb.cp().bin([b]).backgrounds().process_set():
                        rate = cb.cp().bin([b]).process([proc]).GetRate()
                        # if (mass_range=="4500_4750"):
                        print(
                            "For the process..",
                            proc,
                            "...in the bin...",
                            "...rate..",
                            rate,
                        )
                        total_yield += rate
                    if total_yield == 0:
                        # Set a small yield value for each process in the empty bin
                        for proc in cb.cp().bin([b]).backgrounds().process_set():
                            print("Filling the small value for...", proc)
                            cb.cp().bin([b]).process([proc]).ForEachProc(
                                lambda p: p.set_rate(small_value)
                            )
                            print(
                                "After filling the rate = ",
                                cb.cp().bin([b]).process([proc]).GetRate(),
                            )

                    for m in masses:
                        datacard_filename = f"{datacard_dir}/{b}_S0_{m}.txt"
                        print(f">> Writing datacard for bin: {b} and Radionmass: {m}")
                        cb.cp().bin([b]).mass([m, "*"]).WriteDatacard(
                            datacard_filename, output
                        )

                        # Add autoMCStats and rate parameter constraints
                        with open(datacard_filename, "a") as out:
                            out.write(
                                f"rate_top_{find_channel(b)}_{year}_{mass_range} rateParam {b} top 1.0 [0.01,10]\n"
                            )
                            if not args.noAutoMCStats:
                                out.write(f"{b} autoMCStats 50 0 1\n")

            output.Close()

    # Step 2.0: Combine the datacards for each channel for each mass point
    print(
        "\n\n\n\n\n\n\n\n###-->Step 2.0: Combine the datacards for all the bins for each channel for each mass point<--###"
    )
    channels = ["tautau", "leptau"]

    for m in signal_masses:
        for channel in channels:
            print(
                f"\n\n\n      ###-->Processing mass point, combining {channel} for {m}<--###"
            )
            combined_card = (
                f"{combined_dir}/{channel}/combined_{channel}_{year}_{m}.txt"
            )
            os.makedirs(
                f"{combined_dir}/{channel}", exist_ok=True
            )  # Ensure directory exists

            # Find all matching datacards for this channel and mass point
            datacard_files = glob.glob(f"{datacard_dir}/*{channel}*{year}*S0*_{m}*.txt")

            channel_commands = []
            for datacard in datacard_files:
                filename = os.path.basename(datacard)
                channel_name = filename.replace(".txt", "")
                channel_commands.append(f"{channel_name}={datacard}")

            command = f"combineCards.py {' '.join(channel_commands)} > {combined_card}"
            print(f"Running command: {command}")
            run_command(command)

            # Convert to workspace
            workspace_dir_channel = f"{workspace_dir}/{channel}"
            os.makedirs(workspace_dir_channel, exist_ok=True)
            workspace_file = f"{workspace_dir_channel}/combined_{channel}_{m}.root"
            print(
                f"\n\n\n Running the command : text2workspace.py {combined_card} -o {workspace_file} -m {m}"
            )
            run_command(f"text2workspace.py {combined_card} -o {workspace_file} -m {m}")

            # Run combine per channel
            output_dir_channel = f"{output_dir}/{channel}"
            os.makedirs(output_dir_channel, exist_ok=True)
            print(
                f"\n\n\n Running the UNBLINDED LIMIT (channel wise) : combine -M AsymptoticLimits {workspace_file} -m {m} --run blind"
            )
            combine_command = f"combine -M AsymptoticLimits {workspace_file} -m {m} --run blind"
            run_command(combine_command)
            run_command(
                f"mv higgsCombineTest.AsymptoticLimits.mH{m}.root {output_dir_channel}/"
            )

    print(
        "\n\n\n\n\n\n\n\n###-->Step 2.5: Combine the datacards for the three channels for each mass point<--###"
    )
    for m in signal_masses:
        print(f"\n\n\n      ###-->processing mass point, {m}<--###")
        combined_card_full = f"{combined_dir}/combined_{year}_{m}.txt"

        # Edits by Ganesh to custom name the channels for cards being combined
        # Find all matching datacards for this mass point
        datacard_files = glob.glob(f"{datacard_dir}/*{year}*S0*_{m}*.txt")

        # Build the command with custom channel names
        channel_commands = []
        for datacard in datacard_files:
            # Extract the filename without the extension
            filename = os.path.basename(datacard)  # Get the filename only
            channel_name = filename.replace(".txt", "")  # Remove the '.txt' extension
            # Append the channel name and datacard to the command
            channel_commands.append(f"{channel_name}={datacard}")

        # Combine all channel-specific commands into one
        command_full = (
            f"combineCards.py {' '.join(channel_commands)} > {combined_card_full}"
        )
        print(f"Running command: {command_full}")
        run_command(command_full)

        # command_full = f"combineCards.py {datacard_dir}/*{year}*RadionSignal_{m}*.txt > {combined_card_full}"
        # run_command(command_full)

        # End of edits by Ganesh for custom naming of channels for cards being combined

        # Step 3: Convert combined card to workspace and store in workspace directory
        print(
            f"\n\n\n      ###-->Convert combined card to workspace and store in workspace directory for {m}<--###"
        )
        workspace_file = f"{workspace_dir}/combined_{m}.root"
        print(
            f"Running T2W command: ",
            f"text2workspace.py {combined_card_full} -o {workspace_file} -m {m}",
        )
        run_command(
            f"text2workspace.py {combined_card_full} -o {workspace_file} -m {m}"
        )

        # Step 4: Run combine on the workspace using the full path
        print(
            f"\n\n\n      ###-->Run combine on the workspace using the full path for {m}<--###"
        )
        # Run blind
        print(f"Running combine UBLINDED LIMIT: ", combine_command)
        combine_command = f"combine -M AsymptoticLimits {workspace_file} -m {m} --run blind"
        run_command(combine_command)

        # Move output files from combine to the output directory
        print(
            f"\n\n\n      ###-->Move output files from combine to the output directory for {m}<--###"
        )
        run_command(f"mv  higgsCombineTest.AsymptoticLimits.mH{m}.root {output_dir}/")

    # Step 5: Collect limits and plot
    print("\n\n\n\n\n\n\n\n###-->Step 5: Collect limits and plot<--###")
    limit_json = f"{limit_dir}/limits.json"
    run_command(
        f"combineTool.py -M CollectLimits {output_dir}/higgsCombineTest.AsymptoticLimits.mH*.root -o {limit_json}"
    )

    # # Step 6: Modify limits to account for branching ratio
    # print(
    #     "\n\n\n\n\n\n\n\n###-->Step 6: Modify limits to account for branching ratio<--###"
    # )
    # modified_limit_json = f"{limit_dir}/limits_modified.json"
    # modify_limits_json(limit_json, modified_limit_json)

    print("\n\n\n\n\n\n\n\n###-->Step 7: Plot the modified limits using Python 2<--###")
    # plot_command = f"python2 plot_limits_py2.py --json_file {modified_limit_json} --output_dir {limit_dir} --year {year}"
    # run_command(plot_command)
    print("I am printing non modified limits - Please beware if this is not intended")
    # plot_limits(modified_limit_json, limit_dir, year)
    plot_limits(limit_json, limit_dir, year)

    # Collect and modify limits per channel
    for channel in ["leptau", "tautau"]:
        print("Printing limits per channel")
        limit_json_channel = f"{limit_dir}/{channel}/limits.json"
        os.makedirs(f"{limit_dir}/{channel}", exist_ok=True)
        run_command(
            f"combineTool.py -M CollectLimits {output_dir}/{channel}/higgsCombineTest.AsymptoticLimits.mH*.root -o {limit_json_channel}"
        )
        # modified_limit_json_channel = f"{limit_dir}/{channel}/limits_modified.json"
        # modify_limits_json(limit_json_channel, modified_limit_json_channel)
        # print(
        #     "I am printing non modified limits - Please beware if this is not intended"
        # )
        plot_limits(limit_json_channel, f"{limit_dir}/{channel}", year, channel=channel)


if __name__ == "__main__":
    main()
