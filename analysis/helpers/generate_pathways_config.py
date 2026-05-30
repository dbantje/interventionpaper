import pandas as pd
import os
import argparse

parser = argparse.ArgumentParser(
    description="Run premise data package creation from config file."
)
parser.add_argument("--main-scenarios", action="store_true",
                    help="Whether to only run main scenarios. Otherwise, all scenarios in the output folder will be analyzed.")
parser.add_argument("--metals", action="store_true",
                    help="Whether to run analysis for metal extraction indicators.")
parser.add_argument("--MC", action="store_true",
                    help="Whether to run Monte Carlo analysis.")
args = parser.parse_args()

# get list of scenarios to run
MAIN_SCENARIOS = [
    "SSP2-NPi2025-no-interventions",
    "SSP2-PkBudg750-no-interventions",
    "SSP2-PkBudg750-all-interventions"
]
all_scenarios = [
    os.path.join("output", d) for d in os.listdir("output") if "pathways_datapackage.zip" in os.listdir(os.path.join("output", d))
]
if args.main_scenarios:
    scenarios = [
        s for s in all_scenarios if any(ms in s for ms in MAIN_SCENARIOS)
    ]
else:
    scenarios = all_scenarios

# common parameters
years = [2025, 2050]
regions = ["World"]
aggregate_locations = 1
change_pm_compartments = 1
stationary_battery_scen = "CONT"
centralize_subshares = 0
global_subshares = 0
subshares = "no_subshares"
deterministic_categories = "config/deterministic_categories.yml"
lcia = ["metals_grouped"] if args.metals else ["main_methods"]

if args.MC:
    iterations = 500
    remove_uncertainty = 0
    full_distributions = 1
else:
    iterations = 0
    remove_uncertainty = 1
    full_distributions = 0

# build config dataframe
index = pd.MultiIndex.from_product([scenarios, lcia, regions], names = ["scenario", "lcia", "regions"])
df = pd.DataFrame(index = index).reset_index()
df["datapackage"] = df["scenario"].apply(lambda x: x + "/pathways_datapackage.zip")
df["shares"] = subshares
df["years"] = ",".join([str(y) for y in years])
df["iterations"] = iterations
df["aggregate_locations"] = aggregate_locations
df["change_pm_compartments"] = change_pm_compartments
df["stationary_battery_scen"] = stationary_battery_scen
df["full_distributions"] = full_distributions
df["centralize_subshares"] = centralize_subshares
df["apply_subshares_globally"] = global_subshares
df["remove_uncertainty"] = remove_uncertainty
df["deterministic_categories"] = deterministic_categories

# save config to csv
df[
    ["datapackage", "shares", "regions", "lcia", 
    "iterations", "years", "aggregate_locations",
    "change_pm_compartments", "stationary_battery_scen", "full_distributions",
    "centralize_subshares", "apply_subshares_globally", "remove_uncertainty", "deterministic_categories"]
].to_csv("config/pathways_config_generated.csv", sep=";", index=False)