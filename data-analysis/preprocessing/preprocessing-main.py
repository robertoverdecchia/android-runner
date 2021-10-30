import os
import json
import csv
import re


def get_folder_names(path):
    return [name for name in os.listdir(path) if os.path.isdir(os.path.join(path, name))]


# Configuration
phone = "motog5"
raw_data_path = "/Volumes/Seagate HDD/VU/Green Lab/data-main"

# The results will be pushed here before writing them into a csv file at the end
result_rows = []

# Define in which monkey runner scripts the camera/mic are active
monkey_scripts_with_camera_on = ["1", "2"]
monkey_scripts_with_mic_on = ["1", "4"]

# For all folders in the raw data directory:
experiment_setups = get_folder_names(raw_data_path)
for experiment_setup in experiment_setups:
    
    # Read number of participant from folder name (e.g. meet2p -> 2, zoom5p -> 5)
    number_of_participants = re.search(".*([1-9]+)p", experiment_setup).group(1)

    # For all folders in the experiment setup folder
    experiment_runs = get_folder_names(os.path.join(raw_data_path, experiment_setup))
    for experiment_run in experiment_runs:
        # Read config.json to obtain configuration
        config = json.load(open(os.path.join(raw_data_path, experiment_setup, experiment_run, "config.json"),))
        app_name = config["apps"][0]
        duration = config["duration"]

        # Determine which monkey runner script was used here
        monkey_script_path = config["scripts"]["after_launch"][0]["path"]
        monkey_script_number = re.search(".*[meet|zoom]([1-9])\.txt", monkey_script_path).group(1)
        
        # Determine path and file names of energy log files
        log_files_path = os.path.join(raw_data_path, experiment_setup, experiment_run, "data", phone, app_name.replace(".", "-"), "batterystats")
        all_log_files = os.listdir(log_files_path)
        joules_log_files = [f for f in all_log_files if f.startswith("Joule")]
        
        # For all energy measurement log files:
        for file in joules_log_files:
            with open(os.path.join(log_files_path, file)) as csv_file:
                # Read measured energy consumption for each log file
                joules_rows = list(csv.reader(csv_file, delimiter=','))
                joule_value = joules_rows[1][0]

                # Replace the app package by either "Meet" or "Zoom"
                formatted_app_name = {
                    "com.google.android.apps.meetings": "Meet",
                    "us.zoom.videomeetings": "Zoom"
                }[app_name]

                duration_in_minutes = duration / 60000

                # Create a row for each measurement
                result_rows.append({
                    "app": formatted_app_name,
                    "number_of_participants": number_of_participants,
                    "camera": monkey_script_number in monkey_scripts_with_camera_on,
                    "microphone": monkey_script_number in monkey_scripts_with_mic_on,
                    "duration_in_minutes": duration_in_minutes,
                    "joules": joule_value
                })

# Write results to a CSV file
with open(os.path.join(raw_data_path, "..", "results-main.csv"), "w") as f:
    writer = csv.DictWriter(f, fieldnames=["app", "number_of_participants", "camera", "microphone", "duration_in_minutes", "joules"])
    writer.writeheader()
    writer.writerows(result_rows)

print("Done.")