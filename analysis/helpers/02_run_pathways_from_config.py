import pandas as pd
from pathways import Pathways
from pathways.filesystem_constants import DIR_CACHED_DB
import yaml
from shutil import rmtree
import os
from pathlib import Path

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--config", help="Path to the config file", default="config/pathways_config_generated.csv")
parser.add_argument("--suffix", help="Suffix for the output folders", default="main")
args = parser.parse_args()

with open("config/pathways_variable_list.yml", "r") as varfile:
    all_variables = yaml.safe_load(varfile)


selected_methods = yaml.safe_load(open("config/selected_methods.yml", "r"))

methods = {
    "main_methods": selected_methods["main_methods"],
    "metals_grouped": selected_methods["metal_methods"],
}

def get_visible_files(path: str) -> list[Path]:
    """
    Get visible files in a directory.
    :param path: The path to the directory.
    :return: List of visible files.
    """
    return [file for file in Path(path).iterdir() if not file.name.startswith(".")]


def clean_cache_directory(dirpath):
    all_files = get_visible_files(dirpath)
    print("Cleaning cache directory: {}. Number of files to remove: {}".format(dirpath, len(all_files)))
    for file in get_visible_files(dirpath):
        if file.is_dir():
            rmtree(file)
        else:
            file.unlink()

def clean_results_directory(dirpath):
    all_files = get_visible_files(dirpath)
    print("Cleaning results directory: {}. Number of files to remove: {}".format(dirpath, len(all_files)))
    for file in get_visible_files(dirpath):
        if file.is_dir():
            rmtree(file)
        else:
            file.unlink()

CACHEPATHS = [DIR_CACHED_DB]

# read config file
config = pd.read_csv(args.config, delimiter=";", keep_default_na=False, comment="#")

# create output folders
parentfolders = {}
for dp in config["datapackage"].unique():
    dirpath = "/".join(dp.split("/")[:-1]) + f"/results_{args.suffix}"
    if not os.path.exists(dirpath):
        os.mkdir(dirpath)
    else:
        # clean existing results
        clean_results_directory(dirpath)
    parentfolders[dp] = dirpath

# clear cache and old datapackages
for cache_dir in CACHEPATHS:
    clean_cache_directory(cache_dir)


for i, row in config.iterrows():
    # get arguments
    dp = row["datapackage"]
    shares = row["shares"]
    regions = row["regions"]
    lcia = row["lcia"]
    iterations = int(row["iterations"])
    parent_folder = parentfolders[dp]
    years = [int(y) for y in row["years"].split(",")]
    aggregate_locations = (int(row["aggregate_locations"]) == 1)
    change_pm_compartments = (int(row["change_pm_compartments"]) == 1)
    stationary_battery_scen = row["stationary_battery_scen"]
    full_distributions = (int(row["full_distributions"]) == 1)
    centralize_subshares = (int(row["centralize_subshares"]) == 1)
    global_subshares = (int(row["apply_subshares_globally"]) == 1)
    remove_uncertainty = (int(row["remove_uncertainty"]) == 1)
    deterministic_categories = yaml.safe_load(open(row["deterministic_categories"], "r"))

    p = Pathways(datapackage=dp, ecoinvent_version="3.10", clean_cache=False, debug=False,
    classification_system="interventionpaper", stationary_battery_scen=stationary_battery_scen)

    args = {
        "variables": all_variables,
        "years": years,
        "regions": list(regions.split(",")),
        "multiprocessing": False,
        "use_distributions": iterations,
        "remove_uncertainty": remove_uncertainty,
        "change_pm_compartments": change_pm_compartments,
        "full_distributions": full_distributions,
        "log_mc": False,
        "centralize_subshares": centralize_subshares,
        "apply_subshares_globally": global_subshares,
        "deterministic_categories": deterministic_categories,
        "methods": methods[lcia],
    }

    # specify subshare
    if shares == "default":
        shares_fn = "default_shares"
        args.update(
            {
                "subshares": True,
            }
        )
    elif shares == "no_subshares":
        shares_fn = "no_subshares"
        args.update(
            {
                "subshares": False,
            }
        )
    else:
        shares_fn = shares.split("/")[-1].split(".")[0]
        args.update(
            {
                "subshares": True,
            }
        )

    p.calculate(**args)

    p.empty_and_remove_cache()

    # some aggregations
    p.lca_results = p.lca_results.sum(dim=["model", "scenario"])
    if aggregate_locations and not full_distributions:
        p.lca_results = p.lca_results.sum(dim=["location"])


    fname = parent_folder + f"/results_{shares_fn}_{regions}_{lcia}"
    p.export_results(filename=fname)

    # remove datapackage
    rmtree(p.data.base_path, ignore_errors=True)
