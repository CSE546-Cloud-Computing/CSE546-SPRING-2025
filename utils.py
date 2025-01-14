#!/usr/bin/python3

__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

"""
File: utils.py
Author: Kritshekhar Jha
Date: 2025-01-01
Description: Utilities files
"""
import re
import os
import zipfile
import subprocess
import pandas as pd
from grade_project0 import *

def print_and_log(logger, message):
    print(message)
    logger.info(message)

def print_and_log_error(logger, message):
    print(message)
    logger.error(message)

def is_none_or_empty(string):
    return string is None or string.strip() == ""

def write_to_csv(data, csv_path):
    df = pd.DataFrame(data)
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, mode='w', header=True, index=False)

def extract_zip(logger, zip_path, extract_to):
    """Extract the student's zip file."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print_and_log(logger, f"Extracted {zip_path} to {extract_to}")

def find_source_code_path(extracted_folder):
    """Locate the 'source_code' folder inside the extracted directory."""
    for root, dirs, _ in os.walk(extracted_folder):
        if 'credentials' in dirs:
            return os.path.join(root, 'credentials')
    raise FileNotFoundError("source_code folder not found.")

def read_and_extract_credentials(logger, file_path):
    try:
        with open(file_path, 'r') as file:
            contents 	= file.read().strip()
            values 		= contents.split(",")
            print_and_log(logger, f"File: {file_path} has values {tuple(values)}")
            return tuple(values)
    except FileNotFoundError:
        print_and_log_error(logger, f"File not found: {file_path}")
        return None
    except Exception as e:
        print_and_log_error(logger, f"An error occurred: {e}")
        return None

def check_zip_contents(logger, sanity_script, zip_file,results):

    grade_comments      = ""
    sanity_pass         = True
    sanity_status       = ""
    sanity_err          = ""
    script_err          = ""

    try:
        print_and_log(logger, f"Executing {sanity_script} on {zip_file}")

        result          = subprocess.run([sanity_script, zip_file], capture_output=True, text=True, check=True)
        stdout_output   = result.stdout
        stderr_output   = result.stderr
        print_and_log(logger, f"{sanity_script} output:")
        print_and_log(logger, f"{stdout_output}")

        if stderr_output:
            print_and_log_error(logger, f"Script Error: {stderr_output}")

        test_status_pattern = r'\[test_zip_contents\]: (Passed|Failed)'
        match_found         = re.search(test_status_pattern, stdout_output)

        if match_found:
            found_files = match_found.group(1)
            if found_files == "Passed":
                grade_comments  += "Sanity Test Passed: All expected files found.\n"
                sanity_status    = "Pass"
            else:
                sanity_pass          = False
                sanity_status        = "Fail"
                sanity_err          += stdout_output
                sanity_err          += "Sanity Test Failed: All expected files not found.\n"
                grade_comments      += "Sanity Test Failed: All expected files not found.\n"
        else:
            sanity_pass             = False
            sanity_status           = "Fail"
            sanity_err              += stdout_output
            sanity_err              += "Sanity Test Failed: Please inspect manually..\n"
            grade_comments          += "Sanity Test Failed: Please inspect manually..\n"

    except subprocess.CalledProcessError as e:

        print_and_log_error(logger, f"Error executing the {sanity_script} : {e}")
        print_and_log_error(logger, f"Script Error (stderr): {e.stderr}")
        sanity_pass          = False
        sanity_status        = "Fail"
        script_err           = f'{e.stderr}'
        grade_comments      += f'{e.stderr}'
        grade_comments      += f'{e.stdout}'
        results.append(
            {'Name': name, 'ASUID': asuid, 'Test-Sanity': sanity_status,
            'Test-1-score': script_err, 'Test-1-logs': script_err,
            'Test-2-score': script_err, 'Test-2-logs': script_err,
            'Test-3-score': script_err, 'Test-3-logs': script_err,
            'Total Grades':grade_points, 'Comments':grade_comments})

    return sanity_pass, sanity_status, sanity_err, grade_comments, script_err, results
