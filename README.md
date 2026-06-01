# Research code for "Targeted interventions can ensure environmental co-benefits from energy decarbonization"

## Overview

This repository contains research software for the article **"Targeted interventions can ensure environmental co-benefits from energy decarbonization"**.

It uses scenarios from the [REMIND model](https://github.com/remindmodel/remind) to generate prospective LCA databases, and assesses scenario-wide environmental impacts with [Pathways](https://github.com/polca/pathways).



## How to use

### System requirements

This software can be run on a standard computer with Python (version 3.11) installed. It has been tested both on a Windows 10 and a Linux-based Cluster environment.

### Ecoinvent data license

To be able to run the full analysis including prospective LCA (generation of databases  with [Premise](https://github.com/polca/premise) and macro-scale assessment using Pathways), an ecoinvent license valid for version 3.10.1 is needed. Licenses can be purchased at https://ecoinvent.org/licenses/.

### Installing software dependencies

To install the necessary Python dependencies, set up a software environment e.g. with conda

```
conda create --name ENVNAME python=3.11.10 pip
```

activate it using

```
conda activate ENVNAME
```

and install the dependencies

```
pip install -r requirements.txt
```

### Downloading data

To download REMIND scenario files and outputs of Pathways available at https://doi.org/10.5281/zenodo.20458541, run

```
python download_data.py
```

### Generating LCA output

(If you just want to replicate figures, download data and skip this step.)

First set up a Brightway project (fill in your ecoinvent credentials)

```
python 00_setup_ecoinvent.py
```

Then, generate datapackages for Pathways with Premise:

```
python 01_run_premise_from_config.py
```

Lastly, run the scenario-wide assessment with Pathways:

```
python 02_prepare_and_run_pathways.py
```


### Replicating figures

With Pathways output data either re-generated or downloaded, figures from the main text, extended data section, and the SI can be replicated by running the notebooks
- `03a_main_plots.ipynb`
- `03b_extended_data_plots.ipynb`
- `03c_SI_plots.ipynb`


## How to cite this work

David Bantje, Sperring, E., Hahn Menacho, A. J., Sacchi, R., Dürrwächter, J., Rodrigues, R., Müßel, J., Hasse, R., Bauer, C., & Luderer, G. (2026). Research code for "Targeted interventions can ensure environmental co-benefits from energy decarbonization" (v0.9.0). Zenodo. https://doi.org/10.5281/zenodo.20485646

## License

The code contained in this repository is available for use under an [MIT License](https://opensource.org/license/mit).