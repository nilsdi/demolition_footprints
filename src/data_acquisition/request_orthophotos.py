"""
This script is responsible for initializing the download process for orthophotos

It takes in donwload details from downloads at `data/temp/norgeibilder/download_que/'
The downloads that are specified there are then started using the `start_export` function.
The JobID of the download is then saved at `data/temp/norgeibilder/jobids/`
"""
#%% only cell
from src.data_acquisition.orthophoto_api.start_export import start_export, save_export_job
from src.data_acquisition.orthophoto_api.status_export import status_export, save_download_url
from pathlib import Path
import os
import json
import shutil
import time

#%%actually run the script
root_dir = Path(__file__).resolve().parents[2]
download_que_dir = root_dir / "data/temp/norgeibilder/download_que/"
download_que = [d for d in os.listdir(download_que_dir) if ".json" in d] # get all plain json files
for current_export in download_que:
    export_path = download_que_dir / current_export
    with open(export_path, "r") as f:
        export_details = json.load(f)
    JobID = start_export(**export_details)
    save_export_job(JobID, **export_details)
    # move the job to jobids directory
    shutil.move(export_path, download_que_dir/"old_downloads/")


# %%
