import bw2data as bd
import bw2io as bi

ei_version = "3.10.1"
bd.projects.set_current("scenarioLCA_{}".format(ei_version))

# import ecoinvent databases
bi.import_ecoinvent_release(
    version=ei_version,
    system_model="cutoff",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
    use_mp=False,
)