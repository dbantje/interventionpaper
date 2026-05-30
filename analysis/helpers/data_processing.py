import pandas as pd
import numpy as np
import os
import yaml

ENDPOINTS = ["human health", "ecosystem quality"]

REE_ELEMENTS = [
    "Scandium",
    "Yttrium",
    "Lanthanum",
    "Cerium",
    "Praseodymium",
    "Neodymium",
    "Promethium",
    "Samarium",
    "Europium",
    "Gadolinium",
    "Terbium",
    "Dysprosium",
    "Holmium",
    "Erbium",
    "Thulium",
    "Ytterbium",
    "Lutetium"
]

PGM_ELEMENTS = [
    "Platinum",
    "Palladium",
    "Rhodium",
    "Ruthenium",
    "Iridium",
    "Osmium",
]

METALS_SHORTLIST = [
    "Aluminium",
    "Copper",
    "Lead",
    "Lithium",
    "Nickel",
    "Manganese",
    "Zinc",
    "Cobalt",
    "Graphite",
    "REEs",
    "PGMs",
    "Vanadium",
    "Cadmium",
    "Molybdenum",
    "Tantalum",
    "Chromium",
    "Zirconium",
    "Tellurium",
    "Gallium",
    "Indium",
]


def generate_variable_mapping_from_list(varlist, biomass_allocation=False):
    mapping = pd.DataFrame(
        {"variable": varlist}
    )

    def get_sector(v):
        if "SE - cdr" in v:
            sec = "CDR"
        elif "SE - VRE battery storage" in v:
            sec = "VRE battery storage"
        else:
            sec = v.split(" - ")[2]
        if sec == "Transport":
            sec = " - ".join(v.split(" - ")[2:4])
        
        return sec
    
    def get_subsector(v):
        if "Biofuel" in v and biomass_allocation:
            subsec = v.split(" - ")[-3]
        elif "SE -" in v:
            subsec = v.split(" - ")[-1]
        else:
            subsec = v.split(" - ")[-2]
        if subsec == "All steel":
            return "Steel"
        else:
            return subsec
        
    def get_fuel(v):
        if "SE -" in v:
            return ""
        elif "Biofuel" in v:
            if biomass_allocation:
                return " - ".join(v.split(" - ")[-2:])
            else:
                return "Biofuel"
        else:
            return v.split(" - ")[-1]

    mapping["fuel"] = mapping["variable"].apply(get_fuel)
    mapping["sector"] = mapping["variable"].apply(get_sector)
    mapping["subsector"] = mapping["variable"].apply(get_subsector)

    return mapping


def replace_small_activities_with_other(dfall, p=2, exceeded_categories=None):
    """Replace small activities with 'Other' category. Ensure consistency across scenarios by keeping the same set of activities."""
    if exceeded_categories is None:
        exceeded_categories = set()

    for df in dfall:
        # Ensure 'value' is numeric or make NaN
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # Calculate absolute values to avoid small negative values
        df["absolute value"] = np.abs(df['value'].values)
        df["absolute value"] = np.where(df["absolute value"] < 1e-6, 0, df["absolute value"])

        # Calculate the total value for each combination of [year, impact_category]
        df["total"] = df.groupby("year")["absolute value"].transform("sum")
        # Create 'percentage' column in the dataframe
        df["percentage"] = df['absolute value'] / df["total"] * 100
        
        # Track categories that exceed the threshold in this scenario
        for activity in df.loc[df['percentage'] >= p, 'act_category'].unique():
            exceeded_categories.add(activity)

    # Mark as 'Other' any activity that does not exceed the threshold in any year
    for df in dfall:
        df['act_category'] = df['act_category'].apply(
            lambda x: 'Other' if x not in exceeded_categories else x
        )
        df.drop(columns=["absolute value", "percentage", "total"], inplace=True)

    # Return set of categories that exceeded the threshold
    return exceeded_categories


def replace_small_acts(dflist, p=2):
    all_ics = list(dflist[0]["impact_category"].unique())

    combined = []
    for ic in all_ics:
        sel = [df[df["impact_category"] == ic] for df in dflist]
        replace_small_activities_with_other(sel, p=p)
        combined.append(sel)

    # transpose list of lists
    combinedT = list(map(list, zip(*combined)))
    return [pd.concat(l).groupby(
        ["year", "impact_category", "act_category"]
        ).agg({"value": "sum"}).reset_index() for l in combinedT]


def contribution_analysis(df, idx, p):
    # Calculate absolute values to avoid small negative values
    df["absolute value"] = np.abs(df['value'].values)
    # df["absolute value"] = np.where(df["absolute value"] < 1e-8, 0, df["absolute value"])

    # Calculate the total value for each combination of [year, impact_category]
    df["total"] = df.groupby(idx)["absolute value"].transform("sum")
    # Create 'percentage' column in the dataframe
    df["percentage"] = df['absolute value'] / df["total"] * 100

    exceeded_categories = list(df.loc[df['percentage'] >= p, 'act_category'].unique())

    # Mark as 'Other' any activity that does not exceed the threshold in any year
    df['act_category'] = df['act_category'].apply(
        lambda x: 'Other' if x not in exceeded_categories else x
    )
    df.drop(columns=["absolute value", "percentage", "total"], inplace=True)

    return exceeded_categories


def load_data(path):
    if os.path.isdir(path):
        counter = 0
        dflist = []
        for fp in os.listdir(path):
            dflist.append(pd.read_parquet(os.path.join(path, fp)))
            counter += 1
        print(f"{counter} files loaded from {path}.")
        return pd.concat(dflist)
    else:
        return pd.read_parquet(path)


def harmonize_method_name(mstr):
    if mstr.startswith("('") and mstr.endswith("')"):
        return mstr[2:-2].replace("', '", " - ")
    else:
        return mstr
        

def join_indices(dflist):
    large_idx = dflist[0].index
    all_columns = list(dflist[0].columns)
    for df in dflist[1:]:
        large_idx = large_idx.union(df.index)
        all_columns += list(df.columns)
    all_columns = list(set(all_columns))

    zero_df = pd.DataFrame(np.zeros((len(large_idx), len(all_columns))),
                           index=large_idx, columns=all_columns)
    
    return [df.add(zero_df) for df in dflist]


def map_and_reshuffle(dflist, mapping_df):
    data_dict = {}
    for col in mapping_df.columns:
        temp = []
        for df in dflist:
            df[col] = df["variable"].map(mapping_df[col].to_dict())
            temp.append(df.groupby(
            ["year", "impact_category", col]).agg(
                {"value": "sum"}).reset_index())
        data_dict[col] = temp

    return data_dict


def get_endpoint(m):
    if "endpoint" in m:
        return m.split(" - ")[1]
    else:
        return None
    

def get_endpoint_iwp(m):
    for ep in ENDPOINTS:
        if ep in m:
            return ep
        

    
def get_midpoint(m):
    if "endpoint" in m:
        mp = m.split(" - ")[2]
        mp = mp.replace(" no LT", "")
        splits = mp.split(":")
        return splits[0]
        # if splits[0] in ["acidification", "ecotoxicity", "human toxicity", "eutrophication"]:
        #     return mp
        # else:
        #     return splits[0]
    else:
        mp = m.split(" - ")[1]
        return mp


def get_interventionlabel(scen):
    scen2lbl_broad = {
        "lowbio - central": "biomass\nconstraints",
        "wastetreatment - central": "waste\ntreatment",
        "recycling - central": "recycling and\nefficiency",
        "APcontrol - central": "air pollution\ncontrol",
        "1stgenlimit - central": "1st generation\nphaseout",
        "purposelimit - central": "energy crops\nlimit",
        "slag - central": "slag\ntreatment",
        "tailings - central": "tailings\ntreatment",
        "copperrecycling - central": "copper\nrecycling",
        "metalefficiency - central": "metal\nefficiency",
        "otherrecycling - central": "other\nrecycling",
    }

    if scen in scen2lbl_broad:
        return scen2lbl_broad[scen]
    else:
        return scen.replace(" - central", "")
    

def get_midpoint_abbrev(m):
    if m.startswith("ReCiPe"):
        return m.split(" - ")[-1].split("(")[-1][:-1]
    else:
        return "GWP w biog."
    

def get_metal_group(m):
        if m in REE_ELEMENTS:
            return "REEs"
        elif m in PGM_ELEMENTS:
            return "PGMs"
        else:
            return m


def add_midpoint2endpoint(dflist):
    dflist_new = []
    for df in dflist:
        sel = df.copy()
        sel = sel[sel["impact_category"].str.contains("endpoint")]
        sel = sel[~sel["impact_category"].str.contains("total")]
        sel["endpoint"] = sel["impact_category"].apply(get_endpoint)
        sel["midpoint"] = sel["impact_category"].apply(get_midpoint)
        grouped = sel.groupby(["year", "endpoint", "midpoint"]).agg(
            {"value": "sum"}).reset_index()

        dflist_new.append(grouped)

    return dflist_new


def add_midpoint2endpoint_noclimate(dflist):
    dflist_new = []
    for df in dflist:
        sel = df.copy()
        sel = sel[sel["impact_category"].str.contains("endpoint")]
        sel = sel[~sel["impact_category"].str.contains("total")]
        sel = sel[~sel["impact_category"].str.contains("climate change")]
        sel["endpoint"] = sel["impact_category"].apply(get_endpoint)
        sel["midpoint (excl. CC)"] = sel["impact_category"].apply(get_midpoint)
        grouped = sel.groupby(["year", "endpoint", "midpoint (excl. CC)"]).agg(
            {"value": "sum"}).reset_index()

        dflist_new.append(grouped)

    return dflist_new


def add_endpointbymidpointandsector_noclimate(dflist):
    dflist_new = []
    for df in dflist:
        sel = df.copy()
        sel = sel[sel["impact_category"].str.contains("endpoint")]
        sel = sel[~sel["impact_category"].str.contains("total")]
        sel = sel[~sel["impact_category"].str.contains("climate change")]
        sel["endpoint"] = sel["impact_category"].apply(get_endpoint)
        sel["midpoint (excl. CC)"] = sel["impact_category"].apply(get_midpoint)
        grouped = sel.groupby(["year", "endpoint", "midpoint (excl. CC)"]).agg(
            {"value": "sum"}).reset_index()

        dflist_new.append(grouped)

    return dflist_new


def combine_all_data(dflist, mapping_df, p=2):
    data_dict = map_and_reshuffle(dflist, mapping_df)

    data_dict["act_category"] = replace_small_acts(dflist, p=p)
    data_dict["midpoint"] = add_midpoint2endpoint(dflist)
    data_dict["midpoint (excl. CC)"] = add_midpoint2endpoint_noclimate(dflist)

    return data_dict


def prepare_dataframe(
    fname,
    mapping_df=None,
    cols=["variable", "act_category", "year", "impact_category"],
    harmonize_method_names=True,
):  
    # Load results file
    df = load_data(fname)
    if "quantile" in df.columns:
        df = df[df["quantile"] == 0.5]

    # flip value signs for CDR variables
    df["value"] = np.where(df["variable"].str.contains("SE - cdr"), -df["value"], df["value"])

    # add columns by mapping if needed
    mapped_cols = ["sector", "subsector", "fuel", "sector - subsector", "sector - fuel"]
    cols_to_add = [col for col in cols if col in mapped_cols and col not in df.columns]
    if len(cols_to_add) > 0:
        for col in cols_to_add:
            df[col] = df["variable"].map(mapping_df.set_index("variable")[col].to_dict())

    # aggregate to supplied columns
    plot_data = df.groupby(cols).agg(
        {"value": "sum"}).reset_index()
  
    if harmonize_method_names:
        plot_data["impact_category"] = plot_data["impact_category"].apply(harmonize_method_name)
        
    return plot_data


def prepare_data(paths, mapping, p):

    dflist = []
    for fname in paths:
        dflist.append(prepare_dataframe(fname))

    return combine_all_data(dflist, mapping, p=p)


def get_newest_result_folder(scenfolder):
    result_folders = [fp for fp in os.listdir(scenfolder) if fp.startswith("results")]
    if len(result_folders) > 1:
        print("WARNING: More than one result folder; choosing most recent one")
        result_folders.sort(reverse=True)
    
    return os.path.join(scenfolder, result_folders[0])


def get_matching_result_folder(scenfolder, expression):
    matches = [fp for fp in os.listdir(scenfolder) if fp.startswith("results")
               and fp.split("_")[-1] == expression]
    if len(matches) > 1:
        print("WARNING: More than one result folder; choosing alphabetically first.")
        matches.sort(reverse=True)
    
    return os.path.join(scenfolder, matches[0])
    

def get_overview_datapaths(folder, npiname="NPi"):
    searchstrings = {
        "NPi": f"{npiname}-no-interventions",
        "1.5deg_base": "PkBudg650-no-interventions",
        "1.5deg_intervs": "PkBudg650-all-interventions",
    }

    available_scens = [fp for fp in os.listdir(folder)]
    result_folders = []
    for s in searchstrings.values():
        matches = [fp for fp in available_scens if s in fp]
        if len(matches) == 0:
            raise FileNotFoundError(f"No data for {s} in {folder}")
        if len(matches) > 1:
            raise OSError(f"More than one match for {s} in {folder}")
        else:
            scenfolder = os.path.join(folder, matches[0])
            result_folders.append(get_newest_result_folder(scenfolder))

    return result_folders, list(searchstrings.keys())


def get_single_intervention_datapaths(folder, npiname="NPi"):
    single_intervention_scens = [fp for fp in os.listdir(folder) if "intervention" not in fp]
    single_intervention_scens.sort()

    overviewpaths, overviewlabels = get_overview_datapaths(folder, npiname=npiname)

    result_folders = [overviewpaths[1]]
    labels = [overviewlabels[1]]
    for fp in single_intervention_scens:
        result_folders.append(os.path.join(
            folder, fp, get_newest_result_folder(os.path.join(folder, fp))))
        labels.append(fp.split("_")[0][15:])
    result_folders.append(overviewpaths[-1])
    labels.append(overviewlabels[-1])
    
    return result_folders, labels


def build_lbl2fp(output_folder, include_level=True, replace=None):
    lbl2fp = {}
    for fp in os.listdir(output_folder):
        if "NPi" in fp:
            lbl = "NPi"
        elif "PkBudg750-no-interventions" in fp:
            lbl = "1.5deg_base"
        elif "PkBudg750-all-interventions" in fp:
            lbl = "1.5deg_intervs"
        elif "PkBudg750-lowbio-all-interventions" in fp:
            lbl = "1.5deg_biolim_intervs"
        else:
            if include_level:
                scen = fp.split("_")[0]
                intervention = scen.split("-")[2]
                if len(scen.split("-")) == 3:
                    level = "central"
                else:
                    level = scen.split("-")[3]
                lbl = "{} - {}".format(intervention, level)
            else:
                lbl = fp.split("_")[0]
        if replace is not None:
            for old, new in replace.items():
                lbl = lbl.replace(old, new)
        lbl2fp[lbl] = os.path.join(output_folder, fp)
    return lbl2fp


def keep_methods(m, use_adapted_pm, use_adapted_cc):
    if not "endpoint" in m:
        return True
    else:
        if "climate change" in m:
            if use_adapted_cc:
                if "incl. H" in m:
                    return True
                else:
                    return False
            else:
                if "incl. H" in m:
                    return False
                else:
                    return True
        elif "particulate matter formation" in m:
            if use_adapted_pm:
                if "adapted intake fractions" in m:
                    return True
                else:
                    return False
            else:
                if "adapted intake fractions" in m:
                    return False
                else:
                    return True
        else:
            return True
        

def get_plotting_data(
        output_folder,
        scens,
        variable_mapping,
        resultsfolder="main",
        datacols=["sector", "act_category", "year", "impact_category"],
        select_cols = None,
        expected_no_of_result_files=106,
        use_adapted_cc=True,
        use_adapted_pm=True,
        include_level_in_label=True,
        replace_in_label=None,
    ):
    lbl2fp = build_lbl2fp(output_folder, include_level=include_level_in_label, replace=replace_in_label)
    data = []
    if scens == "all":
        scens = list(lbl2fp.keys())
    for scen in scens:
        fp = lbl2fp[scen]
        try:
            fname = get_matching_result_folder(fp, resultsfolder)
        except IndexError as e:
            print(f"WARNING: no matching result folder for {scen} with expression {resultsfolder}. Skipping.")
            continue
        no_results_files = len([fp for fp in os.listdir(fname)])
        if no_results_files != expected_no_of_result_files:
            print(f"WARNING: Folder {fname} contains {no_results_files}," + "\n"
                  + f"not the expected {expected_no_of_result_files} result files. Skipping.")
            continue
            # raise ValueError(f"Folder {fname} contains {no_results_files}, not the expected {expected_no_of_result_files} result files.")
        df = prepare_dataframe(fname, mapping_df=variable_mapping, cols=datacols)
        if select_cols:
            for col, value in select_cols.items():
                df = df[df[col] == value].copy()
        data.append(df)

    filtered_data = {}
    for df, scen in zip(data, scens):
        all_methods = df["impact_category"].unique()
        needed_methods = [m for m in all_methods if keep_methods(m, use_adapted_pm, use_adapted_cc)]
        df = df[df["impact_category"].isin(needed_methods)].copy()
        filtered_data[scen] = df

    return filtered_data


def harmonize_errordata(data, errdata):
    harmonized = {}
    for lbl in data.keys():
        if lbl not in errdata:
            raise ValueError(f"Label {lbl} not found in errdata")
        
        x = errdata[lbl].set_index(["impact_category", "year"]).copy()
        totals = data[lbl].groupby(["impact_category", "year"])["value"].sum()
        medians = errdata[lbl].groupby(["impact_category", "year"])["value"].median()
        scale = totals / medians
        x["value"] = x["value"] * scale.loc[x.index]
        harmonized[lbl] = x.reset_index()

    return harmonized


def get_endpoint_method_groups(df, endpoints):
    all_methods = df["impact_category"].unique()
    mgroups = {}
    for ep in endpoints:
        selection = []
        for m in all_methods:
            if m.split(" - ")[1] == ep:
                selection.append(m)
        mgroups[ep] = selection

    return mgroups


def get_relics_methods(df):
    all_methods = df["impact_category"].unique()
    relics_methods = []
    for m in all_methods:
        if "relics" in m.lower():
            relics_methods.append(m)

    return relics_methods


def get_columnsdata(ddict, scenyearlist, add_midpoints=True, add_metals=False, group_metals=False):
    dflist = []
    for sy in scenyearlist:
        scen = " - ".join(sy.split(" - ")[:-1])
        year = int(sy.split(" - ")[-1])

        df = ddict[scen].copy()
        df = df[df["year"] == year]
        df["scenario-year"] = sy
        if add_midpoints:
            df["midpoint"] = df["impact_category"].apply(get_midpoint)
        if add_metals:
            df["metal"] = df["impact_category"].apply(lambda x: x.split(" - ")[-1])
        if group_metals:
            df["metal"] = df["metal"].apply(get_metal_group)
            df = df[df["metal"].isin(METALS_SHORTLIST)]
        df = df.drop(columns="year")
        dflist.append(df)

    return pd.concat(dflist, ignore_index=True)


def get_reductiondata(ddict, methods, index, columns, p=None):
    dflist = []
    for scen, df in ddict.items():
        sel = df[df["impact_category"].isin(methods)].copy()
        sel["endpoint"] = sel["impact_category"].apply(lambda x: x.split(" - ")[1])
        sel["midpoint"] = sel["impact_category"].apply(get_midpoint)
        sel["scenario"] = scen
        sel = sel.groupby(index+columns)["value"].sum().reset_index()
        dflist.append(sel)

    rdata = pd.concat(dflist)
    if p is not None:
        categories = contribution_analysis(rdata, index, p)
        rdata = rdata.groupby(
            index+columns
        )["value"].sum().reset_index()
        return rdata.pivot(index=index, columns=columns, values="value"), categories
    else:
        return rdata.pivot(index=index, columns=columns, values="value")
    

def get_data_splits_by_midpoint(columnsdata, detail_midpoints, p, fltr=[], mask=[]):
    sel = columnsdata.copy()
    for f in fltr:
        sel = sel[sel["impact_category"].str.contains(f)]
    for m in mask:
        sel = sel[~sel["impact_category"].str.contains(m)]
    sel = sel[sel["midpoint"].isin(detail_midpoints)]

    pdata = {}
    
    # long-term distinction
    shortterm = sel[sel["impact_category"].str.contains("no LT")].groupby(
        ["midpoint", "scenario-year"])["value"].sum()
    full = sel[~sel["impact_category"].str.contains("no LT")].copy()
    fullAgg = full.groupby(
        ["midpoint", "scenario-year"])["value"].sum()
    if len(shortterm) == 0:
        shortterm = pd.Series(0, index=fullAgg.index, dtype=float)
    longterm = fullAgg - shortterm
    pdata["lt"] = pd.DataFrame(
        {
            "short-term": shortterm,
            "long-term": longterm
        }
    )

    # by sector
    grouped = full.groupby(["sector", "scenario-year", "midpoint"])["value"].sum().reset_index()
    pdata["sector"] = grouped.pivot(
        index=["midpoint", "scenario-year"],
        columns="sector",
        values="value"
    )

    # by activity category, go by midpoint
    categories = []
    dflist = []
    for mp in detail_midpoints:
        sel2 = full[full["midpoint"] == mp].copy()
        newcategories = contribution_analysis(sel2, ["scenario-year"], p)
        categories += newcategories
        dflist.append(sel2)
    categories.sort()
    grouped = pd.concat(dflist).groupby(["act_category", "scenario-year", "midpoint"])["value"].sum().reset_index()
    pdata["act_category"] = grouped.pivot(
        index=["midpoint", "scenario-year"],
        columns="act_category",
        values="value"
    ).fillna(0)

    return pdata, categories


def adjacent_values(vals, q1, q3):
    upper_adjacent_value = q3 + (q3 - q1) * 1.5
    upper_adjacent_value = np.clip(upper_adjacent_value, q3, vals[-1])

    lower_adjacent_value = q1 - (q3 - q1) * 1.5
    lower_adjacent_value = np.clip(lower_adjacent_value, vals[0], q1)
    return lower_adjacent_value, upper_adjacent_value


def get_distributions_by_midpoints(columnsdata, detail_midpoints, scenyearlist,fltr=[], mask=[]):
    sel = columnsdata.copy()
    for f in fltr:
        sel = sel[sel["impact_category"].str.contains(f)]
    for m in mask:
        sel = sel[~sel["impact_category"].str.contains(m)]

    distributions = {}
    for mp in detail_midpoints:
        grouped = sel[sel["midpoint"] == mp].groupby(["scenario-year", "sample index"])["value"].sum()
        distributions[mp] = grouped.reset_index().pivot(
            columns="scenario-year", index="sample index", values="value"
        )[scenyearlist].values

    return distributions


def get_stemdata(sdata, idx, scenyearlist, labels, sortlabel=None, idxmap=None):
    baseline = sdata.loc[scenyearlist[0]].groupby(idx).agg({"value": "sum"}).sort_index()
    def ratio(scenyear):
        return sdata.loc[scenyear].groupby(idx).agg({"value": "sum"}).sort_index() / baseline
    
    tempdata = pd.concat((ratio(sy) for sy in scenyearlist[1:]), axis=1)
    pdata = pd.DataFrame(
        tempdata.to_numpy(),
        index=tempdata.index,
        columns=labels
    )

    if sortlabel:
        pdata = pdata.sort_values(by=sortlabel)
    if idxmap is not None:
        pdata.index = pdata.index.map(idxmap)

    return pdata


def get_stemdata_err(sdata, idx, scenyearlist, labels, sortlabel=None, idxmap=None):
    grouped = sdata.groupby(["scenario-year", idx, "sample index"])["value"].sum().unstack("sample index")
    a = grouped.values
    grouped_sorted = pd.DataFrame(
        np.sort(a, axis=1),
        index=grouped.index,
        columns=grouped.columns
    )
    
    baseline = grouped_sorted.loc[scenyearlist[0]]
    def ratio(scenyear):
        return grouped_sorted.loc[scenyear] / baseline
    
    tempdata = pd.concat((ratio(sy).stack() for sy in scenyearlist[1:]), axis=1)
    pdata = pd.DataFrame(
        tempdata.to_numpy(),
        index=tempdata.index,
        columns=labels
    )

    if sortlabel:
        pdata = pdata.sort_values(by=sortlabel)
    if idxmap is not None:
        pdata.index = pdata.index.map(idxmap)

    return pdata


def prepare_waterfall_data(df, index_dict):
    wdata = {}
    for lbl, scen in index_dict.get("start", {}).items():
        wdata[lbl] = df.loc[scen].to_numpy()
    for lbl, slist in index_dict.get("steps", {}).items():
        n = len(slist)
        changes = 0
        for scenA, scenB in slist:
            changes += (df.loc[scenB] - df.loc[scenA]).to_numpy()
        wdata[lbl] = changes / n
    for lbl, scen in index_dict.get("end", {}).items():
        wdata[lbl] = df.loc[scen].to_numpy()
        
    return pd.DataFrame(wdata, index=df.columns).T

def build_waterfall_steps_aumann_shapley(
    scenario_sequence,
    reverse_sequence,
):
    n = len(scenario_sequence) - 1
    steps = []
    for i in range(n):
        forward = (scenario_sequence[i], scenario_sequence[i+1])
        backward = (reverse_sequence[n-i-1], reverse_sequence[n-i])
        steps.append([forward, backward])

    return steps


def build_water_indices(
    scenario_sequence,
    reverse_sequence,
    interventionnames,
    broad_scens,
    startname="1.5°C-base",
    endname="1.5°C-intervs"
):
    # build full sequence of steps
    all_steps = build_waterfall_steps_aumann_shapley(scenario_sequence, reverse_sequence)

    # split into broad steps
    bundles = {name: {} for name in broad_scens}
    counter = 0
    for name, bundlelength in broad_scens.items():
        steps = {}
        for j in range(bundlelength):
            steps[interventionnames[counter]] = all_steps[counter]
            counter += 1
        bundles[name]["steps"] = steps
        bundles[name]["start"] = {}
        bundles[name]["end"] = {}

    # also provide the indices for on the broad level
    n = len(scenario_sequence) - 1
    forward = [scenario_sequence[0]] + [scenario_sequence[counter] for counter in np.cumsum(list(broad_scens.values()))]
    backward = [reverse_sequence[0]] + [reverse_sequence[counter] for counter in np.cumsum(list(broad_scens.values())[::-1])]

    indices = {}
    indices["start"] = {startname: scenario_sequence[0]}
    indices["end"] = {endname: scenario_sequence[-1]}
    indices["steps"] = {
        name: s for name, s in
        zip(broad_scens.keys(), build_waterfall_steps_aumann_shapley(forward, backward))
    }
        
    return indices, bundles

