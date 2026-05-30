from zenodo_get import download
import os
from zipfile import ZipFile
import shutil

ZENODO_DOI = "https://doi.org/10.5281/zenodo.20458541"


def get_zipfile_from_folder(dirpath):
    for filename in os.listdir(dirpath):
        if filename.endswith(".zip"):
            return os.path.join(dirpath, filename)
    raise FileNotFoundError("No zip file found in the directory.")


def copy_contents(src, dest):
    if not os.path.exists(dest):
        os.makedirs(dest)
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dest, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)


if __name__ == "__main__":
    # download the zip file from zenodo
    print("Downloading data from Zenodo...")
    download_folder = "zenodo_download"
    if not os.path.exists(download_folder):
        os.mkdir(download_folder)
    download(ZENODO_DOI, output_dir=download_folder)

    # extract the zip file
    print("Extracting downloaded data...")
    zip_file_path = get_zipfile_from_folder(download_folder)
    with ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(download_folder)

    # move extracted folders
    print("Moving extracted data to target directories...")
    src = os.path.join(download_folder, "remind_runs")
    dest = "data/remind_runs"
    copy_contents(src, dest)
    src = os.path.join(download_folder, "pathways_output")
    dest = "analysis/output"
    copy_contents(src, dest)

    # remove download folder
    print("Removing download folder...")
    shutil.rmtree(download_folder)
