import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch, ArrowStyle, Rectangle
from matplotlib.ticker import ScalarFormatter
import matplotlib.lines as mlines
import colorsys
import seaborn as sns
from data_processing import *
import textwrap
import string

cmap_tab20 = plt.cm.tab20
cmap_set3 = plt.cm.Set3
colors_midpoints = {
    "acidification": cmap_tab20.colors[0],
    "climate change": cmap_tab20.colors[2],
    "ecotoxicity": cmap_tab20.colors[4],
    "eutrophication": cmap_tab20.colors[18],
    "energy resources": cmap_tab20.colors[6],
    "human toxicity": cmap_tab20.colors[8],
    "ionising radiation": cmap_tab20.colors[12],
    "land use": cmap_tab20.colors[16],
    "material resources": cmap_tab20.colors[14],
    "ozone depletion": cmap_set3.colors[11],
    "particulate matter formation": cmap_tab20.colors[10],
    "photochemical oxidant formation": cmap_tab20.colors[17],
    "water use": cmap_tab20.colors[1]
}
midpoint2hex = {mp: mcolors.to_hex(c) for mp, c in colors_midpoints.items()}

# adapt midpoint color map, and create reordered version
midpoint2hex['climate change'] = mcolors.to_rgba(
    midpoint2hex['climate change'], alpha=0.3
)
midpoint2hex_reordered = {}
for k, v in midpoint2hex.items():
    if k != "climate change":
        midpoint2hex_reordered[k] = v
midpoint2hex_reordered["climate change"] = midpoint2hex["climate change"]

# Build up to 30 distinct colors from qualitative palettes
colors = []

# Use high-quality qualitative palettes
palettes = [
    sns.color_palette("Set3", 12),      # 12
    sns.color_palette("Dark2", 8),      # 8
    sns.color_palette("tab10", 10),     # 10
]

# Flatten into one list and trim to 30
for pal in palettes:
    colors.extend(pal)

QUAL_COLORS_20 = colors[:20]
QUAL_COLORS_30 = colors[:30]

QUAL_COLORS_20_no_gray = colors[:8] + colors[9:20]
QUAL_COLORS_30_no_gray = colors[:8] + colors[9:30]

act_categories_sorted = [
    'fossil fuel extraction',
    'nuclear fuel products',
    'agricultural biomass',
    'other waste',
    'slags and other residues',
    'tailings',
    'electricity production',
    'shipping transport',
    'mining and basic metals',
    'minerals',
    'forest biomass',
    'construction',
    'industrial heat',
    'chemicals and plastics',
    'road transport',
    'buildings heat',
    'other metal waste',
    'aviation',
    'oil and gas products',
    'machinery and equipment',
    'other gases',
    'other products',
    'other services',
    'biogas',
    'rail transport',
    'water',
    'biofuel production',
    'coal products',
    'metal products',
    'distribution',
    'pulp and paper',
    'textiles'
]
act2color = {act: QUAL_COLORS_30_no_gray[i%len(QUAL_COLORS_30_no_gray)] for i, act in enumerate(act_categories_sorted)}


# build colormaps
basecolors = {
    "Buildings": '#3fca3f',
    "Industry": '#2fbdbd',
    "Transport - Pass": '#df5152',
    "Transport - Freight": '#7f7f7f',
    "CDR": "#1225ca",
    "VRE battery storage": "#d67f15",
    # "Capacity additions": 
    # "Vehicle sales": 
}

endpoint_colors = {
    "human health": '#df5152',
    "ecosystem quality": "#137c5d",
    "natural resources": "#885717",
}


ENDPOINT2UNIT = {
    "human health": "DALY",
    "ecosystem quality": "species*yr",
    "natural resources": "USD2013",
}


MIDPOINT2UNIT = {
    "human toxicity": "DALY",
    "particulate matter formation": "DALY",
    "land use": "species*yr",
    "material resources": "USD2013",
}

WMIN = 5
WMAX = 95


def get_selected_act_colors(categories):
    cmap = {cat: act2color[cat] for cat in categories}
    cmap['Other'] = QUAL_COLORS_20[8]
    return cmap


def label_axes(axes, position=[-0.05, 1.1], fontsize=12, **kwargs):
    for i, ax in enumerate(axes):
        plbl = string.ascii_lowercase[i]
        ax.text(position[0], position[1], plbl, transform=ax.transAxes, fontsize=fontsize,
                fontweight='bold', va='top', ha='right', **kwargs)


def reverse_cmap(cmap):
    return {k: v for k, v in zip(reversed(cmap.keys()), reversed(cmap.values()))}


def plot_clustered_stacked(dfall, ax, labels=None, legend=True,
                           title="multiple stacked bar plot", H="/", color=None, **kwargs):
    """Given a list of dataframes, with identical columns and index, create a clustered stacked bar plot."""
    n_df = len(dfall)
    n_col = len(dfall[0].columns) 
    n_ind = len(dfall[0].index)

    for df in dfall:  # for each data frame
        if color: # order columns
            ordered_cols = [v for v in color.keys() if v in df.columns]
            df[ordered_cols].plot(kind="bar",
                    linewidth=0,
                    stacked=True,
                    ax=ax,
                    legend=False,
                    grid=False,
                    color=color,
                    **kwargs)  # make bar plots
        else:
            df.plot(kind="bar",
                    linewidth=0,
                    stacked=True,
                    ax=ax,
                    legend=False,
                    grid=False,
                    color=color,
                    **kwargs)  # make bar plots
        
            

    h, l = ax.get_legend_handles_labels()  # get the handles we want to modify
    for i in range(0, n_df * n_col, n_col):  # len(h) = n_col * n_df
        for j, pa in enumerate(h[i:i + n_col]):
            for rect in pa.patches:  # for each index
                rect.set_x(rect.get_x() + 1 / float(n_df + 1) * i / float(n_col))
                rect.set_hatch(H * int(i / n_col))  # edited part     
                rect.set_width(1 / float(n_df + 1))

    ax.set_xticks((np.arange(0, 2 * n_ind, 2) + 0.5 * n_df / float(n_df + 1)) / 2.)
    ax.set_xticklabels(df.index, rotation=0)
    ax.set_title(title)
    ax.set_xbound(lower=-0.3, upper=(n_ind - 0.4))

    # Add invisible data to add another legend
    n = []       
    for i in range(n_df):
        n.append(ax.bar(0, 0, color="gray", hatch=H * i))

    if legend:
        l1 = ax.legend(h[:n_col], l[:n_col], loc='upper left', bbox_to_anchor=(1, 1.03))  #  anchors to top right or use loc=[1.01, 0.15] to position above scenario legend; ncol=ncol
        ax.add_artist(l1)
    if labels is not None:
        l2 = plt.legend(n, labels, loc=[1.01, 0]) # "upper right"


# Function to adjust color shades
def adjust_color_shade(base_color, factor=0.1):
    """
    Adjust the shade of the base color by a factor.
    factor > 0 lightens the color, factor < 0 darkens it.
    """
    base_color = np.array(base_color)
    return np.clip(base_color + factor * (1 - base_color), 0, 1)


# Lighten a color
def lighten_color(color, amount=0.5):
    try:
        c = mcolors.cnames[color]
    except:
        c = color
    rgb = mcolors.to_rgb(c)
    hls = colorsys.rgb_to_hls(*rgb)
    light_rgb = colorsys.hls_to_rgb(hls[0], 1 - amount * (1 - hls[1]), hls[2])
    return light_rgb


def generate_nested_colormap(categories, base_colors, ascending=True, convert2hex=True):
    label_to_color = {}
    for sector, base_color in base_colors.items():
        subsectors = [s for s in categories if s.startswith(sector)]
        n = len(subsectors)
        for i, label in enumerate(subsectors):
            increment = 0.5 * (i / max(1, n - 1))
            if ascending:
                lightness = 0.3 + increment
            else:
                lightness = 0.8 - increment
            label_to_color[label] = lighten_color(base_color, lightness)

    if not convert2hex:
        return label_to_color
    else:
        return {lbl: mcolors.rgb2hex(c) for lbl, c in label_to_color.items()}
    

def gradient_from_base(base_color, n, lighten=True):
    """
    Generate n hex colors in a gradient from the given base_color.
    
    base_color : str (e.g. '#3fca3f')
    n          : int, number of colors to return
    lighten    : if True, fades toward white; if False, darkens toward black
    """
    base_rgb = np.array(mcolors.to_rgb(base_color))
    target_rgb = np.ones(3) if lighten else np.zeros(3)
    
    mix_factors = np.linspace(0, 1, n+1)[:n]
    colors = [
        mcolors.to_hex(base_rgb * (1 - f) + target_rgb * f)
        for f in mix_factors
    ]
    return colors


def many_one_barplot(df, ax, colormap, ticklabels, distributions=None, reference=None, hatches=None):
    x = [0,] + list(range(2, len(df)+1)) 

    if hatches:
        if len(hatches) != len(df.columns):
            raise ValueError(f"Given hatches should be of length {len(df.columns)}, but {len(hatches)} were given.")
    
    ax.set_axisbelow(True)
    bottom_pos = 0
    bottom_neg = 0
    for col in colormap.keys():
        if col in df.columns:
            val = df[col]
            if col == reference:
                ax.scatter(x, val, color=colormap[col], zorder=2, label=reference)
            else:
                bottom = np.where(val >= 0, bottom_pos, bottom_neg)
                patches = ax.bar(x, val, bottom=bottom, color=colormap[col], label=col)
                if hatches:
                    for rect in patches:
                        rect.set_hatch(hatches[col])
                bottom_pos += np.where(val >= 0, val, 0)
                bottom_neg += np.where(val < 0, val, 0)

    if distributions is not None:
        # scale distributions
        # totals = df.sum(axis=1).values
        # medians = np.median(distributions, axis=0)
        # distributions = distributions * (totals / medians)

        # parts = ax.violinplot(
        #     distributions, showmeans=False, showmedians=False,
        #     showextrema=False, positions=x)

        # for pc in parts['bodies']:
        #     pc.set_facecolor("#C0C0C0")
        #     pc.set_edgecolor('black')
        #     pc.set_alpha(1)

        whiskers_min, quartile1, medians, quartile3, whiskers_max = np.percentile(distributions, [WMIN, 25, 50, 75, WMAX], axis=0)
        # whiskers_min, whiskers_max = np.min(distributions, axis=0), np.max(distributions, axis=0)

        # ax.scatter(x, medians, marker='o', color='white', s=30, zorder=3)
        ax.vlines(x, quartile1, quartile3, color='k', linestyle='-', lw=5)
        ax.vlines(x, whiskers_min, whiskers_max, color='k', linestyle='-', lw=1)

    ax.set_xticks(x, ticklabels)
    ax.grid(axis="y")


def preview_colors(label_to_color, title="Some colormap"):
    fig, ax = plt.subplots(figsize=(6, len(label_to_color) * 0.4))
    for i, (label, color) in enumerate(label_to_color.items()):
        ax.barh(i, 1, color=color)
        ax.text(1.05, i, label, va='center')
    ax.set_xlim(0, 2)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title(title)
    plt.tight_layout()
    plt.show()

def endpoint_stackplots(
    data,
    fig,
    endpoints,
    mgroups,
    scenyearlist,
    ticklabels,
    errdata=None,
    scalings={},
    legend_below=False,
    tickrotation=90,
    return_shares=False,
):
    n = len(endpoints)
    x = [0,] + list(range(2, len(scenyearlist)+1))
    yoffset = 0.1 if tickrotation == 0 else 0.23

    pdata = {}
    distributions = {}
    for ep in endpoints:
        mgroup = mgroups[ep]
        sel = data[data["impact_category"].isin(mgroup)]
        if ep in scalings:
            sel["value"] = sel["value"] * scalings[ep]
        grouped = sel.groupby(["scenario-year", "midpoint"])["value"].sum()
        pdata[ep] = grouped.reset_index().pivot(
            index="scenario-year", columns="midpoint", values="value"
        ).loc[scenyearlist]
        if errdata is not None:
            sel = errdata[errdata["impact_category"].isin(mgroup)]
            if ep in scalings:
                sel["value"] = sel["value"] * scalings[ep]
            grouped = sel.groupby(["scenario-year", "sample index"])["value"].sum()
            distributions[ep] = grouped.reset_index().pivot(
                columns="scenario-year", index="sample index", values="value"
            )[scenyearlist].values

    

    axs = fig.subplots(n, 1, sharex=True)
    if len(endpoints) == 1:
        axs = np.array([axs])
    for i, ep in enumerate(endpoints):
        ax = axs[i]
        ax.set_title(ep)
        many_one_barplot(pdata[ep], ax, midpoint2hex_reordered, ticklabels,
                         distributions=distributions.get(ep, None))
        ax.set_ylabel(ENDPOINT2UNIT[ep])
        if not legend_below:
            ypad = yoffset if i == n - 1 else 0.05
            h, l = ax.get_legend_handles_labels()
            l = [textwrap.fill(lbl, 20) for lbl in l]
            ax.legend(h, l, loc="upper right", bbox_to_anchor=(1, -ypad),
                             prop={'size': 8}, ncols=2)

    axs[-1].set_xticks(x, ticklabels, rotation=tickrotation)
            
    if legend_below:
        legend_handles = []
        for mp, c in midpoint2hex_reordered.items():
            if "resources" not in mp:
                legend_handles.append(Patch(color=c, label=mp))
        fig.legend(handles=legend_handles, bbox_to_anchor=(0, -0.02), loc="upper left", ncols=2)

    if return_shares:
        shares = {}
        for ep in endpoints:
            shares[ep] = pdata[ep].div(pdata[ep].sum(axis=1), axis=0)
        return shares


def midpoint_stackplots(
    data,
    fig,
    midpoints,
    scenyearlist,
    ticklabels,
    cols=["lt", "sector", "act_category"],
    errdata=None,
    scalings={},
    p=1,
    top_extend=1.05,
    fallback_unit="unit",
    ic_filter=["endpoint"],
    ic_mask=[],
    legend_y_offset=-0.02,
    act_legend_below=False,
    legend_lw=15,
    tickrotation=90,
    return_shares=False,
    ):
    
    all_categories = []
    x = [0,] + list(range(2, len(scenyearlist)+1))
    yoffset = 0.15 if tickrotation == 0 else 0.33

    # plot
    n = len(midpoints)
    wratios = np.ones(len(cols))
    # if not act_legend_below:
    #     wratios = [1, 1, 1.6]
    axs = fig.subplots(n, len(cols), sharex=True, sharey="row", width_ratios=wratios)

    distributions = {}
    if errdata is not None:
        distributions = get_distributions_by_midpoints(errdata, midpoints, scenyearlist,
                                                       fltr=ic_filter, mask=ic_mask+["no LT"])

    shares = {}
    for i, mp in enumerate(midpoints):
        # get data
        allpdata, categories = get_data_splits_by_midpoint(
            data, [mp], p, fltr=ic_filter, mask=ic_mask
        )
        shares[mp] = {
            dim: allpdata[dim].loc[mp].div(allpdata[dim].loc[mp].sum(axis=1), axis=0)
            for dim in allpdata
        }
        act_colors = get_selected_act_colors(categories)
        all_categories += categories

        errors = distributions.get(mp, None)
        if mp in scalings:
            allpdata = {k: v * scalings[mp] for k, v in allpdata.items()}
            if errors is not None:
                errors = errors * scalings[mp]

        col_counter = 0

        # long-term distinction
        if "lt" in cols:
            pdata = allpdata["lt"].loc[mp]
            ax = axs[i][col_counter]
            mp_color = midpoint2hex[mp]
            colors = {"short-term": mp_color, "long-term": lighten_color(mp_color, 0.5)}
            hatches = {"short-term": "", "long-term": ".."}
            many_one_barplot(pdata.loc[scenyearlist], ax, colors, ticklabels,
                            distributions=errors, hatches=hatches)
            
            if i == 0:
                ax.set_title("by temporal scope")
            n = []       
            for lbl, h in hatches.items():
                n.append(ax.bar(0, 0, color="gray", hatch=h, label=lbl))
            if i == len(midpoints) - 1:
                ax.legend(handles=n, prop={'size': 8}, bbox_to_anchor=(0, -yoffset), loc="upper left")
            col_counter += 1

        # by sector
        if "sector" in cols:
            pdata = allpdata["sector"].loc[mp]
            ax = axs[i][col_counter]
            many_one_barplot(pdata.loc[scenyearlist], ax, basecolors, ticklabels,
                            distributions=errors)
            if i == 0:
                ax.set_title("by sector")
            if i == len(midpoints) - 1:
                legend_handles = []
                for s, c in basecolors.items():
                    legend_handles.append(Patch(color=c, label=s))
                ax.legend(handles=legend_handles, ncols=1, bbox_to_anchor=(0, -yoffset), loc="upper left", prop={'size': 8})
            col_counter += 1

        # by activity
        if "act_category" in cols:
            pdata = allpdata["act_category"].loc[mp]
            ax = axs[i][col_counter]
            many_one_barplot(pdata.loc[scenyearlist], ax, act_colors, ticklabels, 
                            distributions=errors)
            if not act_legend_below:
                h, l = ax.get_legend_handles_labels()
                l = [textwrap.fill(lbl, legend_lw) for lbl in l]
                ax.legend(h, l, loc="upper left", bbox_to_anchor=(1.0, 1), prop={'size': 8})
            if i == 0:
                ax.set_title("by activity category")

        # scale ybounds
        ylim = np.array([ax.get_ylim() for ax in axs[i]]).max(axis=0)
        for ax in axs[i]:
            ax.set_ybound(upper=top_extend * ylim[1])

        unit = MIDPOINT2UNIT.get(mp, fallback_unit)
        ylabel = mp
        if unit is not None:
            ylabel += f"\n[{unit}]"
        axs[i][0].set_ylabel(ylabel)

    for ax in axs[-1]:
        ax.set_xticks(x, ticklabels, rotation=tickrotation)

    if act_legend_below:
        all_categories = list(set(all_categories))
        all_act_colors = get_selected_act_colors(all_categories)
        legend_handles = []
        for a, c in all_act_colors.items():
            legend_handles.append(Patch(color=c, label=a))
        fig.legend(handles=legend_handles, bbox_to_anchor=(0.46, legend_y_offset),
                        loc="upper left", ncols=2, title="activity group")
        
    if return_shares:
        return shares
        

def make_stemplot(
    sdata, ax, scenyearlist,
    errdata=None,
    idx="impact_category",
    labels=["NPi", "1.5deg_base", "1.5deg_intervs"],
    colors=["gray", "C0", "C2"],
    markers=["o", "s", "^"],
    markersize=40,
    markeralpha=0.35,
    plot_reduction=False,
    sortlabel=None,
    reduction_base="NPi",
    reduction_target="1.5deg_base",
    reduction_offset=0.3,
    logscale=False,
    idxmap=None,
    title=None,
    color_by_endpoints=None,
    bracket_offset=3.5,
    patch_width=0.3,
    alpha=0.5,
    ):
    pdata = get_stemdata(sdata, idx, scenyearlist, labels, sortlabel=sortlabel, idxmap=idxmap)
    if errdata is not None:
        pdata_err = get_stemdata_err(errdata, idx, scenyearlist, labels, sortlabel=None, idxmap=idxmap)
    categories = list(pdata.index)

    my_range = np.arange(1, len(pdata .index)+1)[::-1]

    for i, lbl in enumerate(labels):
        malpha = markeralpha if i < len(labels) - 1 else 1
        if errdata is not None:
            distributions = pdata_err[lbl].reset_index().pivot(index=idx, columns="sample index", values=lbl)
            distributions = distributions.reindex(categories).values
            distributions = np.sort(distributions, axis=1)
            whiskersMin, quartile1, medians, quartile3, whiskersMax = np.percentile(distributions, [WMIN, 25, 50, 75, WMAX], axis=1)
            # whiskers_min, whiskers_max = np.min(distributions, axis=1), np.max(distributions, axis=1)
            whiskers = np.array([
                adjacent_values(sorted_array, q1, q3)
                for sorted_array, q1, q3 in zip(distributions, quartile1, quartile3)])
            whiskersMin, whiskersMax = whiskers[:, 0], whiskers[:, 1]

            ax.scatter(pdata[lbl], my_range, marker='|', color=colors[i], s=80, zorder=3, label=lbl)
            ax.hlines(my_range, quartile1, quartile3, color=colors[i], linestyle='-', lw=5, alpha=markeralpha, zorder=2)
            ax.hlines(my_range, whiskersMin, whiskersMax, color=colors[i], linestyle='-', lw=1, alpha=markeralpha)
        else:
            ax.scatter(pdata[lbl], my_range, label=lbl, zorder=i+2,
                   color=colors[i], alpha=malpha, marker=markers[i], s=markersize)
            
    if errdata is None:
        ax.hlines(
            y=my_range,
            xmin=[min(x, 1) for x in pdata[labels[0]]],
            xmax=[max(x, 1) for x in pdata[labels[0]]],
            color='grey', alpha=0.4, zorder=0)
    ax.axvline(x=1, ls="dashed", alpha=0.4, zorder=0, color="gray")

    if plot_reduction:
        poscolor = plt.cm.coolwarm(0.75)
        negcolor = plt.cm.coolwarm(0.25)
        y = len(categories)
        for base, target in zip(pdata[reduction_base], pdata[reduction_target]):
            linecolor = negcolor if base > target else poscolor
            ax.annotate(
                "",
                xy=(base, y+reduction_offset),
                xytext=(target, y+reduction_offset),
                ha="center", va="center",
                arrowprops=dict(arrowstyle='<-', shrinkA=0, shrinkB=0,color=linecolor),
                zorder=0
            )
            y -= 1

    if logscale:
        ax.set_xscale("log")
    ax.set_yticks(my_range, categories)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    if title is not None:
        ax.set_title(title)

    if color_by_endpoints == "box":
        for txt, cat in zip(ax.get_yticklabels(), categories):
            txt.set_bbox(dict(facecolor=endpoint_colors[cat], alpha=alpha, edgecolor='none'))
    elif color_by_endpoints == "bracket":
        for i, ep in enumerate(endpoint_colors.keys()):
            color = endpoint_colors[ep]
            mps = list(sdata[sdata["endpoint"] == ep]["midpoint"].unique())
            for j, cat in enumerate(categories):
                if cat in mps:
                    p = Rectangle(
                        (-bracket_offset + patch_width*(i-3), (len(categories) - 0.5 -j)),
                        patch_width,
                        1,
                        transform=ax.get_yaxis_transform(),
                        color=color, alpha=alpha,
                        clip_on=False, zorder=3
                    )
                    ax.add_patch(p)


def reduction_heatmap(
    rdata,
    intervention_groups,
    refscen="1.5deg_base",
    cmap="RdBu_r",
    normthresh=0.001,
    include_sum=True,
    ):
    # calculate reductions and totals
    reductions = rdata - rdata.loc[refscen]
    totals = rdata.loc[refscen].sum(axis=1)
    if include_sum:
        reductions["sum"] = reductions.sum(axis=1)

    # collect data by endpoint
    endpoints = rdata.index.get_level_values("endpoint").unique()
    pdata = {
        ep: reductions.xs(ep, level="endpoint").dropna(axis="columns", how="all") / totals.loc[ep]
        for ep in endpoints
    }

    # prepare colormaps
    v = max([np.max(np.abs(df.values)) for df in pdata.values()])
    norm = mcolors.SymLogNorm(normthresh, vmin=-v, vmax=v)

    # set up figure and plot
    fsize = (12, len(endpoints)*3.5 + 1)
    fig, axs = plt.subplots(len(endpoints), len(intervention_groups),
                            sharex="col", sharey="row", figsize=fsize,
                            width_ratios = [len(v) for v in intervention_groups.values()])
    if len(endpoints) == 1:
        axs = np.array([axs])
    if len(intervention_groups) == 1:
        axs = np.array([axs]).T

    for j, group in enumerate(intervention_groups.keys()):
        for i, ep in enumerate(pdata.keys()):
            ax = axs[i][j]
            if i == 0:
                ax.set_title(group)
            if j == 0:
                ax.set_ylabel(ep)

            interventions = intervention_groups[group]
            hm_data = pdata[ep].loc[interventions]

            hm = sns.heatmap(
                hm_data.T,
                ax=ax,
                cmap=cmap,
                norm=norm,
                cbar=False,
                linewidths=1.5,
                linecolor="lightgray"
            )


def reduction_tornadochart(
    rdata,
    intervention_groups,
    cmap,
    sharey="row",
    refscen="1.5deg_base",
    ):
    # calculate reductions and totals
    reductions = rdata - rdata.loc[refscen]
    totals = rdata.loc[refscen].sum(axis=1)
    reductions["sum"] = reductions.sum(axis=1)

    # collect data by endpoint
    endpoints = rdata.index.get_level_values("endpoint").unique()
    pdata = {
        ep: reductions.xs(ep, level="endpoint").dropna(axis="columns", how="all") / totals.loc[ep]
        for ep in endpoints
    }

    # set up figure and plot
    fsize = (12, len(endpoints)*3.5 + 1)
    fig, axs = plt.subplots(len(endpoints), len(intervention_groups),
                            sharex="col", sharey=sharey, figsize=fsize,
                            width_ratios = [len(v) for v in intervention_groups.values()])
    if len(endpoints) == 1:
        axs = np.array([axs])
    if len(intervention_groups) == 1:
        axs = np.array([axs]).T

    for j, group in enumerate(intervention_groups.keys()):
        for i, ep in enumerate(pdata.keys()):
            ax = axs[i][j]
            if i == 0:
                ax.set_title(group)
            if j == 0:
                ax.set_ylabel(ep)

            interventions = intervention_groups[group]
            tornado_data = pdata[ep].loc[interventions].drop(columns="sum")
            tornado_data.plot.bar(stacked=True, ax=ax, color=cmap, legend=False)
            

def double_bar_plot_v3(df, y, ax, cmap1, cmap2, barwidth=0.3, spacing_factor=0.15, textpadding=0.03):
    spacing = barwidth * spacing_factor
    y1 = y + (barwidth + spacing) / 2
    y2 = y - (barwidth + spacing) / 2
    ytext = y + 1.2 * (barwidth + spacing)

    left = 0
    for j, idx in enumerate(df.index):
        sel = df.loc[idx].copy()

        left1 = left
        left2 = left
        for col1, color1 in cmap1.items():
            # plot bars for first set of categories
            if col1 in sel.index.levels[0]:
                sel1 = sel.loc[col1].copy()
                widths1 = sel1.sum()
                # print(col1, widths1)
                ax.barh(y1, widths1, left=left1, color=color1, height=barwidth)

                for col2, color2 in cmap2.items():
                    # plot bars for second set of categories
                    if col2 in sel1.index:
                        widths2 = sel1.loc[col2]
                        ax.barh(y2, widths2, left=left2, color=color2, label=col2, height=barwidth)
                        left2 += widths2
                
                left1 += widths1
                ax.vlines(left1, y2 - barwidth/2, y2 + barwidth/2, color="black", linewidth=0.5)

        ax.text(left + sel.sum() / 2, ytext, idx, va="bottom", ha="center",
                fontsize=8, clip_on=False, backgroundcolor="white")
        left += sel.sum()
        if j < len(df.index) - 1:  # avoid drawing line after the last bar
            ax.vlines(left, y2 - 1.2 * (barwidth + spacing) / 2, y1 + 1.2 * (barwidth + spacing) / 2,
                      color="black", linewidth=1.5, ls="--")


def reduction_tornadochart_twoway(
    rdata,
    intervention_groups,
    endpoints,
    errdata=None,
    refscen="1.5deg_base",
    bwidth=0.8,
    gs_wspace=0.05,
    gs_hspace=0.05,
    p=4,
    **kwargs,
    ):
    # calculate reductions and totals
    reductions = rdata - rdata.loc[refscen]
    totals = rdata.loc[refscen].sum(axis=1)

    if errdata is not None:
        reductionsErr = errdata - errdata.loc[refscen]

    # set up figure and plot
    fsize = (12, len(endpoints)*4.5 + 1)
    fig = plt.figure(figsize=fsize)
    gs = fig.add_gridspec(len(intervention_groups) * len(endpoints), 3, width_ratios=[0.4, 0.6, 0.2],
    wspace=gs_wspace, hspace=gs_hspace)

    # build axes for actual plots
    axsLeft = []
    axsRight = []
    for i in range(len(endpoints)):
        axsLeft.append(fig.add_subplot(gs[i * len(intervention_groups):(i + 1) * len(intervention_groups), 0]))
        axsRight.append(fig.add_subplot(gs[i * len(intervention_groups):(i + 1) * len(intervention_groups), 1]))

    for ax in axsLeft:
        ax.sharex(axsLeft[-1])
    for i, ax in enumerate(axsRight):
        ax.sharex(axsRight[-1])
        ax.sharey(axsLeft[i])

    # broad intervention plots
    all_handles = []
    for i, ep in enumerate(endpoints):
        sel = reductions.xs(ep, level="endpoint").dropna(axis="columns", how="all") / totals.loc[ep]

        # broad interventions
        ax = axsLeft[i]
        interventions = list(intervention_groups.keys())[::-1]
        longsel = sel.melt(ignore_index=False).reset_index()
        broad_data = longsel.groupby(["scenario", "midpoint"])["value"].sum().reset_index().pivot(
            index="scenario", columns="midpoint", values="value"
        ) * 100
        
        broad_data.loc[interventions].plot.barh(stacked=True, ax=ax, color=midpoint2hex_reordered,
                                                legend=True, width=bwidth, position=0.5)
        if errdata is not None:
            selErr = reductionsErr.xs(ep, level="endpoint").dropna(axis="columns", how="all") / totals.loc[ep]
            selErr = selErr * 100
            distributions = selErr.sum(axis=1).unstack("sample index").loc[interventions].values

            y = np.arange(len(interventions))[::-1]
            whiskers_min, quartile1, medians, quartile3, whiskers_max = np.percentile(distributions, [2, 25, 50, 75, 98], axis=1)
            ax.hlines(y, quartile1, quartile3, color='k', linestyle='-', lw=5)
            ax.hlines(y, whiskers_min, whiskers_max, color='k', linestyle='-', lw=1)

        h, l = ax.get_legend_handles_labels()
        l = [textwrap.fill(lbl, 20) for lbl in l]
        ax.legend(h, l, loc="lower left", prop={'size': 8})
        ax.set_yticklabels([get_interventionlabel(scen) for scen in interventions])
        yticks = ax.get_yticks()[::-1]
        ax.set_ylabel(ep)
        if i == 0:
            ax.set_title("broad interventions")
        if i == len(endpoints) - 1:
            ax.set_xlabel("reduction relative to\n1.5°C base scenario [%]")

        # shares of single interventions
        ax = axsRight[i]
        for k, group in enumerate(intervention_groups.keys()):
            interventions = intervention_groups[group]
            if ep == "ecosystem quality" and group == "APcontrol - central":
                interventions = [iv for iv in interventions if iv != "woodstoves - central"]
            y = yticks[k] - bwidth/6
            true_reductions = - sel.where(sel < 0, 0)
            longsel2 = true_reductions.loc[interventions].melt(ignore_index=False).reset_index()
            longsel2["scenario"] = longsel2["scenario"].apply(get_interventionlabel)
            act_cats = contribution_analysis(longsel2, "scenario", p=p)
            act_colors = get_selected_act_colors(act_cats)
            longsel2 = longsel2.groupby(["scenario", "midpoint", "act_category"])["value"].sum().reset_index()
            pivot = longsel2.pivot(index="scenario", columns=["midpoint", "act_category"], values="value") / np.abs(longsel2["value"].sum())
            double_bar_plot_v3(
                100 * pivot, y, ax, reverse_cmap(midpoint2hex_reordered), act_colors, barwidth=bwidth/3, **kwargs
            )
            # create a legend
            lax = fig.add_subplot(gs[i * len(intervention_groups) + k, 2])
            lax.axis("off")
            legend_handles = []
            for a, c in act_colors.items():
                legend_handles.append(Patch(color=c, label=textwrap.fill(a, 15)))
            lax.legend(handles=legend_handles, loc="center left", prop={'size': 8}, ncols=2)

        if i == 0:
            ax.set_title("intervention contributions")
        if i == len(endpoints) - 1:
            ax.set_xlabel("share of intervention group [%]")
            ax.set_xticks([0, 25, 50, 75, 100])


def waterfall_barplot_helper(wdata, ax, cmap, ticklabels, barwidth, include_start_and_end=True):
    sorted_columns = [c for c in cmap.keys() if c in wdata.columns]

    x = np.arange(len(wdata)-2)
    bottoms = list(wdata.cumsum().sum(axis=1))[:-2]
    if include_start_and_end:
        x = np.arange(len(wdata))
        bottoms = [0] + bottoms + [0]
    
    # bottom_neg = bottoms.copy()
    # bottom_pos = bottoms.copy()
    # positive part
    pos = wdata.where(wdata >= 0, 0).reindex(columns=sorted_columns)
    neg = wdata.where(wdata < 0, 0).reindex(columns=sorted_columns[::-1])

    if include_start_and_end:
        pos.plot.bar(stacked=True, ax=ax, color=cmap, bottom=bottoms,
                                 legend=False, width=barwidth)
        neg.plot.bar(stacked=True, ax=ax, color=cmap, bottom=bottoms,
                                 legend=False, width=barwidth)
    else:
        pos.iloc[1:-1].plot.bar(stacked=True, ax=ax, color=cmap, bottom=bottoms,
                                 legend=False, width=barwidth)
        neg.iloc[1:-1].plot.bar(stacked=True, ax=ax, color=cmap, bottom=bottoms,
                                 legend=False, width=barwidth)

    # for col in cmap.keys():
    #     if col in wdata.columns:
    #         val = wdata[col]
    #         bottom = np.where(val >= 0, bottom_pos, bottom_neg)
    #         ax.bar(x, val, bottom=bottom, color=cmap[col], label=col)
    #         bottom_pos += np.where(val >= 0, val, 0)
    #         bottom_neg += np.where(val < 0, val, 0)

    if not include_start_and_end:
        ticklabels = ticklabels[1:-1]
    ax.set_xticks(x, ticklabels, rotation=90)
    ax.grid(axis="y")


def make_waterfall_chart_new(df, ax, cmap, indices, barwidth=0.6, arrowwidth=1.0, include_start_and_end=True):
    wdata = prepare_waterfall_data(df, indices)

    # get order of bars
    sorted_columns = [c for c in cmap.keys() if c in wdata.columns][::-1]
    wdata = wdata[sorted_columns]

    # calculate bottoms for stacked bars and let all bars start from the the bottom
    waterfall_barplot_helper(
        wdata, ax, cmap, wdata.index, barwidth, include_start_and_end=include_start_and_end
    )

    # # 
    # if include_start_and_end:
    #     wdata.plot.bar(stacked=True, ax=ax, color=cmap, bottom=bottoms,
    #                             legend=False, width=barwidth)
    # else:
    #     wdata.iloc[1:-1].plot.bar(stacked=True, ax=ax, color=cmap, bottom=bottoms[1:-1],
    #                             legend=False, width=barwidth)

    # add line and arrows
    totals = wdata.cumsum().sum(axis=1)
    offset = 0 if include_start_and_end else -1
    astyle = ArrowStyle.BarAB(widthA=arrowwidth, widthB=arrowwidth)
    astyle = "->, head_width=0.4"
    for i, y in enumerate(totals):
        # ax.plot([i, i+1.5], [y, y], color="black", zorder=0, lw=0.8)
        if i == 0:
            continue
        prev_y = totals.iloc[i-1]
        if y > prev_y:
            ax.annotate("", xy=(i+0.5+offset, y), xytext=(i+0.5+offset, prev_y),
            arrowprops=dict(arrowstyle=astyle, color="black", shrinkA=0, shrinkB=0))
        else:
            ax.annotate("", xy=(i+0.5+offset, y), xytext=(i+0.5+offset, prev_y),
            arrowprops=dict(arrowstyle=astyle, color="black", shrinkA=0, shrinkB=0))

    # extend xlim
    if not include_start_and_end:
        left, right = ax.get_xlim()
        ax.set_xlim(right=right+0.2)

    return wdata.cumsum().iloc[:-1]


def reductions_waterfalls_new(
    rdata,
    indices_broad,
    intervention_bundles,
    cmap,
    idx,
    refscen="1.5deg_base",
    legend_below=False,
):
    # data in percentages of reference scenario
    totals = rdata.loc[refscen].sum(axis=1)
    rdata = rdata.div(totals, axis=0) * 100

    # set up figure
    fig = plt.figure(layout="constrained", figsize=(12, 9))
    if legend_below:
        gs = fig.add_gridspec(2, 2, wspace=0, width_ratios=[0.4, 0.6], height_ratios=[len(idx), 0.3])
        sfigLeft = fig.add_subfigure(gs[:, 0])
        sfigRight = fig.add_subfigure(gs[0, 1])
        sfigLegend = fig.add_subfigure(gs[1, 1])
    else:
        gs = fig.add_gridspec(2, 2, wspace=0, width_ratios=[0.4, 0.6])
        sfigLeft = fig.add_subfigure(gs[:, 0])
        sfigRight = fig.add_subfigure(gs[:, 1])

    fig.supylabel("Relative change to NZ in 2050 [%]")

    
    axsLeft = sfigLeft.subplots(len(idx), 1, sharex=True)

    # plot waterfall charts for each endpoint for broad categories
    dflist = []
    for id, ax in zip(idx, axsLeft):
        sel = rdata.xs(id, level=1).dropna(axis="columns", how="all")
        wdata = make_waterfall_chart_new(sel, ax, cmap, indices_broad, arrowwidth=0.8)
        wdata["endpoint"] = id
        wdata["scenario"] = [f"After {i} broad steps" for i in range(len(wdata))]
        dflist.append(wdata.set_index(["scenario", "endpoint"]))
        ax.set_title(id)
        if not legend_below:
            h, l = [], []
            for mp, c in cmap.items():
                if mp in sel.columns:
                    h.append(Patch(color=c))
                    l.append(mp)
            ax.legend(h, l, loc="lower center", prop={"size": 9})
        ax.set_ylim(0, 105)

    # updates left and right bars for bundles
    for i, group in enumerate(intervention_bundles.keys()):
        start = f"After {i} broad steps"
        end = f"After {i+1} broad steps"
        intervention_bundles[group]["start"] = {start: start}
        intervention_bundles[group]["end"] = {end: end}

    # add intermediate steps to data
    intermediates = pd.concat(dflist)
    rdata = pd.concat([rdata, intermediates])

    axsRight = sfigRight.subplots(len(idx), len(intervention_bundles), sharex="col", sharey=False)

    for i, id in enumerate(idx):
        for j, group in enumerate(intervention_bundles.keys()):
            ax = axsRight[i][j]
            indices = intervention_bundles[group]
            sel = rdata.xs(id, level=1).dropna(axis="columns", how="all")
            make_waterfall_chart_new(sel, ax, cmap, indices, arrowwidth=0.5, include_start_and_end=False)
            if i == 0:
                ax.set_title(group)
            if j == 0:
                ax.set_ylabel(id)

            # scale y limits
            low, high = ax.get_ybound()
            if j == 0:
                high = 100
            extend = 0.05 * (high - low)
            ax.set_ylim(low, high+extend)
            
                
    if legend_below:
        legend_handles = []
        for mp, c in cmap.items():
            legend_handles.append(Patch(color=c, label=mp))
        sfigLegend.legend(handles=legend_handles, bbox_to_anchor=(0, 1.0),
                        loc="upper left", ncols=3, title="midpoint")
  


def get_max_halfrange(
    sdata, scenyearlist, idx,
    labels,
    cmap_base,
    range_base,
    labels_plot,
    ):  
    # rename keys
    sdata_new = {k: sdata.loc[sy] for k, sy in zip(labels, scenyearlist)}

    # calculate ratios
    baseline = sdata_new[range_base].groupby(idx).agg({"value": "sum"}).sort_index()
    def ratio(lbl):
        return sdata_new[lbl].groupby(idx).agg({"value": "sum"}).sort_index() / baseline
    
    tempdata = pd.concat((ratio(lbl) for lbl in labels), axis=1)
    pdata = pd.DataFrame(
        tempdata.to_numpy(),
        index=tempdata.index,
        columns=labels
    )

    max_halfrange = 0
    for i, lbl in enumerate(labels_plot):
        colors = np.log10(pdata[lbl] / pdata[cmap_base])
        halfrange = np.abs(colors).max()
        if halfrange > max_halfrange:
            max_halfrange = halfrange

    return max_halfrange


def make_stemplot_brokenaxis(
    sdata, fig, scenyearlist,
    breakx=[2.5, 5.5],
    hratios=[1, 1],
    rlim_extend=1.05,
    indices=["endpoint", "midpoint"],
    labels=["NPi", "1.5deg_base", "1.5deg_intervs"],
    colors=["gray", "C0", "C2"],
    markers=["o", "s", "^"],
    markersize=40,
    markeralpha=0.5,
    plot_reduction=False,
    reduction_base="NPi",
    reduction_target="1.5deg_base",
    reduction_offset=0.3,
    logscale=False,
    idxmap=None,
    titles=None,
    ticklength=20,
    color_by_endpoints=["box", "bracket"],
    bracket_offset=3.5,
    patch_width=0.3,
    alpha=0.5,
    ):
    # get data
    data = {idx: get_stemdata(sdata, idx, scenyearlist, labels, idxmap) for idx in indices}
    rlim = max(df.max().max() for df in data.values()) * rlim_extend
    splitlength = max(breakx[0], rlim - breakx[1])

    # set up axes
    axs = fig.subplots(nrows=len(indices), ncols=2, sharex="col", sharey=False, height_ratios=hratios)
    fig.subplots_adjust(wspace=0.1)

    for i, idx in enumerate(indices):
        if titles:
            axs[i, 0].text(titles[i])

        # get the data
        pdata = get_stemdata(sdata, idx, scenyearlist, labels, idxmap)
        categories = list(pdata.index)
        my_range = np.arange(1, len(pdata.index)+1)[::-1]

        # iterate over parts of broken axis to plot
        for j in range(2):
            ax = axs[i, j]

            # scatter plots
            for k, lbl in enumerate(labels):
                malpha = markeralpha if k < len(labels) - 1 else 1
                ax.scatter(pdata[lbl], my_range, label=lbl, zorder=k+2,
                        color=colors[k], alpha=malpha, marker=markers[k], s=markersize)
            
            # stems and lines
            ax.hlines(
                y=my_range,
                xmin=[min(x, 1) for x in pdata[labels[0]]],
                xmax=[max(x, 1) for x in pdata[labels[0]]],
                color='grey', alpha=0.4, zorder=0)
            ax.axvline(x=1, ls="dashed", alpha=0.4, zorder=0, color="gray")

            ax.set_ylim(0.5, len(categories)+0.5)

            if plot_reduction:
                poscolor = plt.cm.coolwarm(0.75)
                negcolor = plt.cm.coolwarm(0.25)
                y = len(categories)
                for base, target in zip(pdata[reduction_base], pdata[reduction_target]):
                    linecolor = negcolor if base > target else poscolor
                    ax.annotate(
                        "",
                        xy=(base, y+reduction_offset),
                        xytext=(target, y+reduction_offset),
                        ha="center", va="center",
                        arrowprops=dict(arrowstyle='<-', shrinkA=0, shrinkB=0, color=linecolor),
                        zorder=0
                    )
                    y -= 1

        # adjustments for broken axis
        ax1 = axs[i, 0]
        ax2 = axs[i, 1]
        ax1.set_xlim(0, splitlength)
        ax2.set_xlim(rlim-splitlength, rlim)
        ax1.spines.right.set_visible(False)
        ax2.spines.left.set_visible(False)
        ax1.yaxis.tick_left()
        # ax2.tick_params(axis='y', which='both', right=False)  # don't put tick labels on the right
        ax1.set_yticks(my_range, [textwrap.fill(cat, ticklength) for cat in categories])
        ax2.set_yticks([])  # remove y-ticks from the right subplot

        # slanted lines
        d = .5  # proportion of vertical to horizontal extent of the slanted line
        kwargs = dict(marker=[(-d, -1), (d, 1)], markersize=12,
                    linestyle="none", color='k', mec='k', mew=1, clip_on=False)
        ax1.plot([1, 1], [0, 1], transform=ax1.transAxes, **kwargs)
        ax2.plot([0, 0], [0, 1], transform=ax2.transAxes, **kwargs)

        if color_by_endpoints[i] == "box":
            for txt, cat in zip(ax1.get_yticklabels(), categories):
                txt.set_bbox(dict(facecolor=endpoint_colors[cat], alpha=alpha, edgecolor='none'))
        elif color_by_endpoints[i] == "bracket":
            for i, ep in enumerate(endpoint_colors.keys()):
                color = endpoint_colors[ep]
                mps = list(sdata[sdata["endpoint"] == ep]["midpoint"].unique())
                for j, cat in enumerate(categories):
                    if cat in mps:
                        p = Rectangle(
                            (-bracket_offset + patch_width*(i-3), (len(categories) - 0.5 -j)),
                            patch_width,
                            1,
                            color=color, alpha=alpha,
                            clip_on=False, zorder=3
                        )
                        ax1.add_patch(p)


def make_stemplot_cmap(
    sdata, ax, scenyearlist,
    labels, labels_plot,
    cmap_base,
    range_base,
    sort_base,
    idx="impact_category",
    cmap="coolwarm",
    norm=plt.Normalize,
    markers=["o", "^"],
    markersize=40,
    markeralpha=1.0,
    logscale=False,
    idxmap=None,
    title=None,
    color_by_endpoints=None,
    bracket_offset=0.35,
    patch_width=0.03,
    alpha=0.5,
    ):
    # rename keys
    sdata_new = {k: sdata.loc[sy] for k, sy in zip(labels, scenyearlist)}
  
    # calculate ratios
    baseline = sdata_new[range_base].groupby(idx).agg({"value": "sum"}).sort_index()
    def ratio(lbl):
        return sdata_new[lbl].groupby(idx).agg({"value": "sum"}).sort_index() / baseline
    
    tempdata = pd.concat((ratio(lbl) for lbl in labels), axis=1)
    pdata = pd.DataFrame(
        tempdata.to_numpy(),
        index=tempdata.index,
        columns=labels
    )

    pdata = pdata.sort_values(by=sort_base)
    if idxmap is not None:
        pdata.index = pdata.index.map(idxmap)
    categories = list(pdata.index)

    my_range = np.arange(1, len(pdata .index)+1)[::-1]

    for i, lbl in enumerate(labels_plot):
        colors = pdata[lbl] / pdata[cmap_base]
        ax.scatter(pdata[lbl], my_range, label=lbl, zorder=i+2,
                   c=colors, cmap=cmap, norm=norm, alpha=markeralpha, marker=markers[i], s=markersize)

    ax.hlines(
        y=my_range,
        xmin=[min(x, 1) for x in pdata[sort_base]],
        xmax=[max(x, 1) for x in pdata[sort_base]],
        color='grey', alpha=0.4, zorder=0)
    ax.axvline(x=1, ls="dashed", alpha=0.4, zorder=0, color="gray")

    if logscale:
        ax.set_xscale("log")
    ax.set_yticks(my_range, categories)
    ax.set_ylim(0.5, len(categories)+0.5)
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    if title is not None:
        ax.set_title(title)

    if color_by_endpoints == "box":
        for txt, cat in zip(ax.get_yticklabels(), categories):
            txt.set_bbox(dict(facecolor=endpoint_colors[cat], alpha=alpha, edgecolor='none'))
    elif color_by_endpoints == "bracket":
        for i, ep in enumerate(endpoint_colors.keys()):
            color = endpoint_colors[ep]
            mps = list(sdata[sdata["endpoint"] == ep]["midpoint"].unique())
            for j, cat in enumerate(categories):
                if cat in mps:
                    p = Rectangle(
                        (-bracket_offset + patch_width*(i-3), (len(categories)-0.5-j)),
                        patch_width,
                        1,
                        color=color, alpha=alpha,
                        clip_on=False, zorder=3
                    )
                    ax.add_patch(p)  


def get_vmin_vmax(
    sdata, scenyearlist, idx,
    labels,
    cmap_base,
    range_base,
    labels_plot,
    ):  
    # rename keys
    sdata_new = {k: sdata.loc[sy] for k, sy in zip(labels, scenyearlist)}

    # calculate ratios
    baseline = sdata_new[range_base].groupby(idx).agg({"value": "sum"}).sort_index()
    def ratio(lbl):
        return sdata_new[lbl].groupby(idx).agg({"value": "sum"}).sort_index() / baseline
    
    tempdata = pd.concat((ratio(lbl) for lbl in labels), axis=1)
    pdata = pd.DataFrame(
        tempdata.to_numpy(),
        index=tempdata.index,
        columns=labels
    )

    vmin = (pdata[labels_plot] / pdata[cmap_base]).min().min()
    vmax = (pdata[labels_plot] / pdata[cmap_base]).max().max()
    
    return vmin, vmax


def get_max_scaling(
    sdata, scenyearlist, idx,
    labels,
    cmap_base,
    range_base,
    labels_plot,
):
    # rename keys
    sdata_new = {k: sdata.loc[sy] for k, sy in zip(labels, scenyearlist)}

    # calculate ratios
    baseline = sdata_new[range_base].groupby(idx).agg({"value": "sum"}).sort_index()
    def ratio(lbl):
        return sdata_new[lbl].groupby(idx).agg({"value": "sum"}).sort_index() / baseline
    
    tempdata = pd.concat((ratio(lbl) for lbl in labels), axis=1)
    pdata = pd.DataFrame(
        tempdata.to_numpy(),
        index=tempdata.index,
        columns=labels
    )

    max_scaling = 1
    for lbl in labels_plot:
        ratio = pdata[lbl] / pdata[cmap_base]
        scale = max(ratio.max(), ratio.min())
        if scale > max_scaling:
            max_scaling = scale

    return max_scaling


def get_gray_legend_markers(labels, markers, markersize=7):
    handles = []
    for m, lbl in zip(markers,labels):
        handles.append(mlines.Line2D([], [], marker=m, color="grey", linestyle='None', markersize=markersize, label=lbl))
    return handles


def check_error_harmonization(columns_data, columns_errdata, mgroup):
    sel = columns_data[columns_data["impact_category"].isin(mgroup)]
    selErr = columns_errdata[columns_errdata["impact_category"].isin(mgroup)]
    sel["IC"] = sel["impact_category"].apply(lambda x: x.split(" - ")[-1])
    selErr["IC"] = selErr["impact_category"].apply(lambda x: x.split(" - ")[-1])

    # normalize
    totals = sel.groupby(["scenario-year", "IC"])["value"].sum()
    selErr = selErr.pivot(
        index=["scenario-year", "IC"],
        columns="sample index",
        values="value"
    )
    selErr = selErr.div(totals, axis=0)

    sns.catplot(
        data=selErr.melt(ignore_index=False).reset_index(),
        x="IC",
        y="value",
        col="scenario-year",
        col_wrap=2,
        kind="violin"
    )



