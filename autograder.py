#!/usr/bin/python3

__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

"""
File: grade_project0.py
Author: Kritshekhar Jha
Description: Autograder for Project-1
"""

import re
import os
import sys
import pdb
import ast
import glob
import time
import shutil
import zipfile
import logging
import argparse
import subprocess
import pandas as pd
import importlib.util

from utils import *
from cloudwatch import *
from grade_project1 import *
from validate_permission_policies import *

parser = argparse.ArgumentParser(description='Upload images')
parser.add_argument('--img_folder', type=str, help='Path to the input images')
parser.add_argument('--pred_file', type=str, help='Classfication results file')
args = parser.parse_args()
img_folder = args.img_folder
pred_file  = args.pred_file

log_file = 'autograder.log'
logging.basicConfig(filename=log_file, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# CSV Files and Paths
grade_project           = "Project-1"
project_path            = os.path.abspath(".")
roster_csv              = 'class_roster.csv'
grader_results_csv      = f'{grade_project}-grades.csv'
zip_folder_path         = f'{project_path}/submissions'
sanity_script           = f'{project_path}/test_zip_contents.sh'
grader_script           = f'{project_path}/grade_project0.py'

print_and_log(logger, f'+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++')
print_and_log(logger, "- 1) The script will first look up for the zip file following the naming conventions as per project document")
print_and_log(logger, "- 2) The script will then do a sanity check on the zip file to make sure all the expected files are present")
print_and_log(logger, "- 3) Extract the credentials from the credentials.txt")
print_and_log(logger, "- 4) Execute the test cases as per the Grading Rubrics")
print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

print_and_log(logger, f'++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++')
print_and_log(logger, f"Project Path: {project_path}")
print_and_log(logger, f"Grade Project: {grade_project}")
print_and_log(logger, f"Class Roster: {roster_csv}")
print_and_log(logger, f"Zip folder path: {zip_folder_path}")
print_and_log(logger, f"Test zip contents script: {sanity_script}")
print_and_log(logger, f"Grading script: {grader_script}")
print_and_log(logger, f"Test Image folder path: {img_folder}")
print_and_log(logger, f"Classification results file: {pred_file}")
print_and_log(logger, f"Autograder Results: {grader_results_csv}")
print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

roster_df   = pd.read_csv(roster_csv)
results     = []

if os.path.exists(grader_results_csv):
    #todo
    pass
else:
    print_and_log(logger, f"The file {grader_results_csv} does NOT exist.")

for index, row in roster_df.iterrows():

    first_name = row['First Name']
    last_name  = row['Last Name']

    name    = f"{row['Last Name']} {row['First Name']}"
    #name    = f"{row['Last Name']} {row['First Name']}".lower()
    #name    = name.replace(' ', '').replace('-', '')
    asuid   = row['ASUID']

    print_and_log(logger, f'++++++++++++++++++ Grading for {last_name} {first_name} ASUID: {asuid} +++++++++++++++++++++')

    start_time = time.time()
    grade_points        = 0
    grade_comments      = ""
    results             = []
    pattern             = os.path.join(zip_folder_path, f'*{asuid}*.zip')
    zip_files           = glob.glob(pattern)

    if zip_files and os.path.isfile(zip_files[0]):

        zip_file            = zip_files[0]
        sanity_pass         = True
        sanity_status       = ""
        sanity_err          = ""
        kernel_module_pass  = True

        # STEP-1: Validate the zip file
        test_pass, test_status, test_err, test_comments, test_script_err, test_results  = check_zip_contents(logger, sanity_script, zip_file, results)

        sanity_pass     = test_pass
        sanity_status   = test_status
        sanity_err      += test_err
        grade_comments  += test_comments
        results         = test_results

        if sanity_pass:

            sanity_comment = "Unzip submission and check folders/files: PASS"
            print_and_log(logger, sanity_comment)

            extracted_folder = f'extracted'
            del_directory(logger, extracted_folder)
            extract_zip(logger, zip_file, extracted_folder)
            directories, files = find_source_code_path(extracted_folder, ["credentials/credentials.txt", "web-tier/server.py"])

            credentials_path     = directories[0]
            credentials_txt_path = files[0]

            print_and_log(logger, f"This is the submission file path: {credentials_path}")

            if not os.path.exists(credentials_path):
                print_and_log_error(logger, f"Credentials path does not exist: {credentials_path}")
                raise FileNotFoundError(f"Credentials path does not exist: {credentials_path}")

            # Check if credentials.txt exits
            if not os.path.exists(credentials_txt_path):
                print_and_log_error(logger, f"credentials.txt not found in {credentials_path}")
                raise FileNotFoundError(f"credentials.txt not found in {credentials_path}")

            print_and_log(logger, f"Found credentials.txt  at {credentials_path}")
            cred_values = read_and_extract_credentials(logger,credentials_txt_path)

            try:
                # STEP-2: Validate the credentials.txt
                if (len(cred_values) == 3 and is_none_or_empty(cred_values[0]) == False and is_none_or_empty(cred_values[1]) == False
                                          and is_none_or_empty(cred_values[2]) == False):
                    print_and_log(logger, "Credentials parsing complete.")
                else:
                    print_and_log_error(logger, "Issue with credentials submitted. Points: [0/100]")
                    grade_comments += f"Issue with submitted credentials. Credentials Found : {cred_values}"
                    tc_2_pts = tc_3_pts = grade_points = 0
                    results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                                "Fail",   grade_comments, tc_2_pts, grade_comments,
                                                tc_3_pts, grade_comments, grade_points, grade_comments)
                    write_to_csv(results, grader_results_csv)
                    continue

                try:
                    # STEP-3: Validate the permission policies
                    iam_obj = iam_policies(logger, cred_values[0], cred_values[1])
                    iam_ro_access_flag, ec2_ro_access_flag, s3_full_access_flag = iam_obj.validate_policies()

                    if (iam_ro_access_flag == False):
                        print_and_log_warn(logger, "IAMReadOnlyAccess not attached.")

                    # STEP-4: Validate the billing alarm
                    cloudwatch_obj  = aws_cloudwatch(logger, cred_values[0], cred_values[1])
                    cloudwatch_obj.main()

                    # STEP-5: Execute test cases
                    aws_grader    = grader_project1(logger, asuid, cred_values[0], cred_values[1], ec2_ro_access_flag, s3_full_access_flag)
                    ip_addr       = cred_values[2]
                    test_results  = aws_grader.main(ip_addr, img_folder, pred_file)
                    grade_points  = test_results["grade_points"]

                    grade_comments += test_results["tc_2"][1]
                    grade_comments += test_results["tc_3"][1]

                    results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                            "Pass", "IAMReadOnlyAccess attached", test_results["tc_2"][0], test_results["tc_2"][1],
                                            test_results["tc_3"][0], test_results["tc_3"][1], grade_points, grade_comments)

                except ClientError as e:
                    print_and_log_error(logger, f"Failed to fetch the attached polices. {e}")
                    print_and_log_error(logger, f"Total Grade Points: {grade_points}")
                    grade_comments += f"Failed to fetch attached policies. {e}"
                    tc_2_pts = tc_3_pts = grade_points = 0
                    results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                                "Fail",   grade_comments, tc_2_pts, grade_comments,
                                                tc_3_pts, grade_comments, grade_points, grade_comments)

            except subprocess.CalledProcessError as e:
                print_and_log_error(logger, "Error encountered while grading. Please inspect the autograder logs..")

            # Clean up: remove the extracted folder
            try:
                shutil.rmtree(extracted_folder)
                print_and_log(logger, f"Removed extracted folder: {extracted_folder}")
            except Exception as e:
                print_and_log_error(logger, f"Could not remove extracted folder {extracted_folder}: {e}")
        else:
            sanity_comment = "Unzip submission and check folders/files: FAIL"
            print_and_log_error(logger, sanity_comment)
            grade_comments += sanity_comment
            tc_2_pts = tc_3_pts = grade_points = 0
            results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                                "Fail",   grade_comments, tc_2_pts, grade_comments,
                                                tc_3_pts, grade_comments, grade_points, grade_comments)
            logger.handlers[0].flush()

    else:
        sanity_status           = False
        sanity_comment          = f"Submission File (.zip) not found for {asuid}."
        print_and_log_error(logger, sanity_comment)
        grade_comments      += "{sanity_comment} There is a possiblity that student has misspelled their asuid"
        tc_2_pts = tc_3_pts = grade_points = 0
        results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                        "Fail",   grade_comments, tc_2_pts, grade_comments,
                                        tc_3_pts, grade_comments, grade_points, grade_comments)

    write_to_csv(results, grader_results_csv)

    # End timer
    end_time = time.time()

    # Calculate and print execution time
    execution_time = end_time - start_time
    print_and_log(logger, f"Execution Time for {last_name} {first_name} ASUID: {asuid}: {execution_time} seconds")
    print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.handlers[0].flush()

print_and_log(logger, f"Grading complete for {grade_project}. Check the {grader_results_csv} file.")
