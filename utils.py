#!/usr/bin/python3

"""
File: utils.py
Author: Kritshekhar Jha
Date: 2025-01-01
Description: Utils
"""
import re
import os
import shutil
import zipfile
import subprocess
import pandas as pd
from grade_project_p2_p2 import *

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

def validate_num_requests(value):
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError(f"num_requests must be at least 1, but got {ivalue}")
    return ivalue

def extract_zip(logger, zip_path, extract_to):
    """Extract the student's zip file."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print_and_log(logger, f"Extracted {zip_path} to {extract_to}")

def del_directory(logger, directory_name):
    try:
        if os.path.exists(directory_name) and os.path.isdir(directory_name):
            shutil.rmtree(directory_name)
            print_and_log(logger, f"Removed extracted folder: {directory_name}")
    except Exception as e:
        print_and_log_error(logger, f"Could not remove extracted folder {directory_name}: {e}")

def find_source_code_path(extracted_folder):
    """Locate the 'source_code' folder inside the extracted directory."""
    for root, dirs, _ in os.walk(extracted_folder):
        if 'credentials' in dirs:
            return os.path.join(root, 'credentials')
    raise FileNotFoundError("source_code folder not found.")

def read_and_extract_file(logger, file_path):
    try:
        with open(file_path, 'r') as file:
            if file_path == "extracted/credentials/credentials.txt":
                contents 	= file.read().strip()
                values 		= contents.split(",")
                print_and_log(logger, f"File: {file_path} has values {tuple(values)}")
                return tuple(values)
            else:
                return "Other files found!"
    except FileNotFoundError:
        print_and_log_error(logger, f"File not found: {file_path}")
        return None
    except Exception as e:
        print_and_log_error(logger, f"An error occurred: {e}")
        return None

def append_grade_remarks(results, name, asuid, tc_0_status, tc_0_logs, tc_1_status, tc_1_logs,
                        tc_2_pts, tc_2_logs,
                        tc_3_pts, tc_3_logs,
                        grade_points, grade_comments):

    results.append({'Name': name, 'ASUID': asuid, 'Test-0': tc_0_status, 'Test-0-logs': tc_0_logs,
                    'Test-1': tc_1_status, 'Test-1-logs': tc_1_logs,
                    'Test-2-score': tc_2_pts, 'Test-2-logs': tc_2_logs,
                    'Test-3-score': tc_3_pts, 'Test-3-logs': tc_3_logs,
                    'Total Grades':grade_points, 'Comments':grade_comments})
    return results
