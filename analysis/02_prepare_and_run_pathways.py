import os

# main methods for all scenarios
cmd = "python helpers/generate_pathways_config.py"
os.system(cmd)
cmd = "python helpers/02_run_pathways_from_config.py"
os.system(cmd)

# metals for main scenarios
cmd = "python helpers/generate_pathways_config.py --metals"
os.system(cmd)
cmd = "python helpers/02_run_pathways_from_config.py --suffix metals"
os.system(cmd)

# MC runs for main scenarios
cmd = "python helpers/generate_pathways_config.py --MC"
os.system(cmd)
cmd = "python helpers/02_run_pathways_from_config.py --suffix MC"
os.system(cmd)

# MC metals runs for main scenarios
cmd = "python helpers/generate_pathways_config.py --MC --metals"
os.system(cmd)
cmd = "python helpers/02_run_pathways_from_config.py --suffix metalsMC"
os.system(cmd)