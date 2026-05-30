
from premise import PathwaysDataPackage, clear_cache, clear_inventory_cache
import bw2data as bd

import os
from datetime import datetime

import os
import pandas as pd

import argparse


ALL_INTERVENTIONS = [
    "tailings",
    "slags",
    "copper",
    "smelting",
    "woodstoves",
    "shipping",
]

# avoid doubly adjusting emission factors
GAINS_MASKS = [
    "burned in container ship",
    "smelting of copper concentrate, sulfide ore",
    "heat production, hardwood chips from forest, at furnace 50kW",
    "heat production, mixed logs, at wood heater"
]

FILEPATH_ADJUSTED_SECONDARY_SHARES = "./config/adjusted_secondary_shares.csv"
OUTPUT_DIR = "./output/"

def extract_folder_and_scenario(fp, model="remind"):
    fname = (fp.split("/")[-1]).split(".")[0]
    folder = "/".join(fp.split("/")[:-1])
    scen = fname.replace(model+"_", "")

    return folder, scen

def get_new_version_number():
    previous_versions = []
    for name in os.listdir("output"):
        fp = "output/" + name
        if os.path.isdir(fp) and name != "archive":
            previous_versions.append(name.split("p")[0][1:])

    return max([int(v) for v in previous_versions]) + 1

def get_intervention_scenarios(s):
    if s == "":
        return {}
    elif "all" in s:
        scen = s.split(":")[1]
        return {intervention: scen for intervention in ALL_INTERVENTIONS}
    else:
        intervention_scenarios = {}
        for x in s.split(","):
            intervention = x.split(":")[0]
            scen = x.split(":")[1]
            intervention_scenarios[intervention] = scen
        return intervention_scenarios


def get_group_shares(df, group, scen):
    if group == "all":
        sel = df
    else:
        if group not in df["group"].unique():
            raise ValueError(f"Group {group} not found in {FILEPATH_ADJUSTED_SECONDARY_SHARES}."
                            + "Please check the group names in the file and the config.")
        sel = df[df["group"] == group]

    shares = {}
    baseline = sel.set_index("metal")["frozen"].to_dict()
    if scen in sel.columns:
        s = sel.set_index("metal")[scen].to_dict()
        for metal, s in s.items():
            bl = baseline[metal]
            shares[metal] = {
                "secondary": {2020: bl, 2050: s},
                "primary": {2020: 1 - bl, 2050: 1 - s}
            }
    elif scen == "intervention":
        metals = sel["metal"]
        means = sel["central"]
        minima = sel["low"]
        maxima = sel["high"]
        for metal, mean, min_, max_ in zip(metals, means, minima, maxima):
            shares[metal] = {
                "secondary": {
                    2020: {"mean": baseline[metal], "min": baseline[metal], "max": baseline[metal]},
                    2050: {"mean": mean, "min": min_, "max": max_}
                },
                "primary": {
                    2020: {"mean": 1 - baseline[metal], "min": 1 - baseline[metal], "max": 1 - baseline[metal]},
                    2050: {"mean": 1 - mean, "min": 1 - max_, "max": 1 - min_}
                }
            }

    return shares


def get_shares_adjustments(s):
    adjustments = pd.read_csv(FILEPATH_ADJUSTED_SECONDARY_SHARES, delimiter=";")
    shares_adjustments = get_group_shares(adjustments, "all", "frozen")
    if s != "":
        for x in s.split(","):
            group, scen = x.split(":")
            new_shares = get_group_shares(adjustments, group, scen) # check if groups and scenarios are valid
            shares_adjustments.update(new_shares)
    
    return shares_adjustments

parser = argparse.ArgumentParser(description="Run premise data package creation from config file.")
parser.add_argument("--config", type=str, default="config/premise_config_v10.csv",
                    help="Path to the config file. Default is config/premise_config.csv.")
parser.add_argument("--clear_inventory_cache", action="store_true",
                    help="Whether to clear the inventory cache before running." \
                    "Use this if you want to make sure all inventories are re-imported," \
                    "but it will increase runtime significantly.")
parser.add_argument("--clear_full_cache", action="store_true",
                    help="Whether to clear the full cache before running." \
                    "Use this if you want to make sure all source databases and inventories are re-imported," \
                    "but it will increase runtime significantly.")
parser.add_argument("--model", type=str, default="remind",
                    help="Model name for the scenario input. Default is 'remind'.")
parser.add_argument("--years", type=str, default="2025,2050",
                    help="Years for the premise runs. Default is '2025,2050'.")
parser.add_argument("--keep_uncertainty", type=str, default="biosphere,technosphere",
                    help="Matrices for which to keep the uncertainty data from the source database. " \
                    "Options are 'biosphere', 'technosphere', or both separated by comma. ")
args = parser.parse_args()

# read in config
config = pd.read_csv(args.config, delimiter=";", keep_default_na=False, comment="#")

# create new output folder
outputdir = "output/"
if not os.path.exists(outputdir):
    os.mkdir(outputdir)

# clear caches if indicated
if args.clear_full_cache:
    print("Clearing full cache...")
    clear_cache()
elif args.clear_inventory_cache:
    print("Clearing inventory cache...")
    clear_inventory_cache()

sectors = [
    "biomass",
    "electricity",
    "cement",
    "steel" ,
    "fuels",
    "renewable",
    "metals",
    "interventions",
    "heat",
    "cdr",
    "battery",
    "emissions",
    "cars",
    "two_wheelers",
    "trucks",
    "ships",
    "buses",
    "trains",
    "final energy",
]


# setup brightway project
ei_version = "3.10.1"
bd.projects.set_current("scenarioLCA_{}".format(ei_version))

print(f"Running premise data package creation for {len(config)} scenarios.")

for idx, row in config.iterrows():
    start = (row["start"] == 1)
    title = row["title"]
    years = list(args.years.split(","))

    # skip indicated runs
    if not start:
        print(f"Run {title} will be skipped.")
        continue

    # get transformations
    if row["exclude_sectors"] == "":
        transformations = sectors
    else:
        excluded_sectors = list(row["exclude_sectors"].split(","))
        transformations = [s for s in sectors if s not in excluded_sectors]
        print(f"Excluding updates of sectors {excluded_sectors}.")

    # add capacity splitting if needed
    if row["split_capacity"] != 1:
        transformations = [s for s in transformations if s != "capacity"]
        print("Excluding capacity split operation.")

    metals_scenario = "default"
    if row["metals_scenario"] != "":
        metals_scenario = row["metals_scenario"]

    fleet_regionalization = "global"
    if row["fleet_regionalization"] != "":
        fleet_regionalization = row["fleet_regionalization"]

    gains_scenario = row["gains_scenario"]
    intervention_scenarios = get_intervention_scenarios(row["interventions"])
    shares_adjustments = get_shares_adjustments(row["shares_adjustments"])

    # shared arguments
    kwargs = {
        "years": years,
        "source_db": f"ecoinvent-{ei_version}-cutoff",
        "source_version": "3.10",
        "use_absolute_efficiency": True,
        "gains_scenario": gains_scenario,
        "gains_baseyear": 2020,
        "gains_masks": GAINS_MASKS,
        "metals_scenario": metals_scenario,
        "fleet_regionalization": fleet_regionalization,
        "intervention_scenarios": intervention_scenarios,
        "shares_adjustments": shares_adjustments,
        "biosphere_name": f"ecoinvent-{ei_version}-biosphere",
        "keep_source_db_uncertainty": list(args.keep_uncertainty.split(",")) if args.keep_uncertainty != "" else [],
    }

    runs_dir, scen = extract_folder_and_scenario(row["filepath"], model=args.model)
    print(f"Creating data package for scenario {scen} with scenario input at {runs_dir}.")
    scenario = {"model": args.model, "pathway": scen, "filepath": runs_dir}
    kwargs["scenarios"] = [scenario]

    ndb = PathwaysDataPackage(**kwargs)

    dirname = f"{title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.mkdir(outputdir + dirname)

    fname = "pathways_datapackage"
    ndb.create_datapackage(
        name=outputdir+f"{dirname}/{fname}",
        transformations=transformations
    )





