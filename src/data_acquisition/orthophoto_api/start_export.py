import requests
import json
import os
import time

def start_export(project:str, resolution:float, format:int = 4, compression_method:int = 5,
                         compression_value:float = 50, mosaic:bool = False)->int:
    '''
    Request an export of the orthophoto project specified.
    The export JobID returned can be used to fetch the status of the export.
    User and password are taken from the geonorge_login.json file.

    Arguments:
    - project: The project ID of the orthophoto to be exported.
    - resolution: The resolution of the orthophoto to be exported in meters.
    - format: The format of the orthophoto to be exported (see documentation for details).
    - compression_method: The compression method to be used for the export (see doc).
    - compression_value: The compression value to be used for the export (see doc).
    - mosaic: Whether to export the orthophoto as a mosaic or not - not yet implemented.
    
    Returns:
    - The JobID of the export request.
    '''
    rest_export_url = "https://tjenester.norgeibilder.no/rest/startExport.ashx"

    # Get the directory of this file
    parent_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the JSON file
    json_file_path = os.path.join(parent_dir, 'geonorge_login.json')

    # Open the JSON file
    with open(json_file_path, 'r') as file:
        # Load the JSON data
        login = json.load(file)

    export_payload  = {
    "Username": login['Username'],
    "Password": login['Password'],
    'CopyEmail': 'nils.dittrich@ntnu.no',
    "Format": format,
    'Resolution': resolution,
    'CompressionMethod': str(compression_method),
    'CompressionValue': str(compression_value),
    "Projects": project, 
    'Imagemosaic': 2, # 2 means no mosaic
    'support_files': 1 # medata or not - we choose yes
    }
    # we need to send the payload as a json in a request calling it the request
    export_payload_json = json.dumps(export_payload)
    export_query = {"request": export_payload_json}
    export_response = requests.get(rest_export_url, params = export_query)

    if export_response.status_code != 200:
        raise Exception(f"Export request failed with status code {export_response.status_code}.")
    else:
        JobID = export_response.json()['JobID']

    return JobID

# remove whitespace from name
# change coordinate system WSG84
# proof the path stuff (for servers?)

def save_export_job(JobID:int, project:str, resolution:float, 
                                compression_method:int, compression_value:float, mosaic:bool)->None:
    '''
    Save the export job details to a file for later reference.

    Arguments:
    - JobID: The JobID of the export request.
    - project_name: The name of the orthophoto project to be exported.
    - resolution: The resolution of the orthophoto to be exported in meters.
    - compression_type: The compression method to be used for the export.
    - compression_value: The compression value to be used for the export.
    - mosaic: Whether to export the orthophoto as a mosaic or not.
    
    Returns:
    - None
    '''
    greatgrandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd())))

    # current time for the file name
    current_time = time.strftime("%Y%m%d-%H%M%S")
    file_name = f"Export_{project.lower()}_{current_time}.json"
    file_path =  greatgrandparent_dir + f"/data/temp/norgeibilder/jobids/" + file_name 

    if compression_method != 5:
        raise Exception("Only LZW compression (type 5) is supported in saving the job at the moment.")
    
    export_job = {
        "JobID": JobID,
        "project": project,
        "resolution": resolution,
        "compression_method": compression_method,
        "compression_value": compression_value,
        "mosaic": mosaic
    }

    with open(file_path, 'w') as file:
        json.dump(export_job, file)

    return