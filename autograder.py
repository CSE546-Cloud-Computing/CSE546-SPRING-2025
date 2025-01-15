#!/usr/bin/python3

__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

"""
File: autograder.py
Author: Kritshekhar Jha
Date: 2025-01-01
Description: Autograder for Project-0
"""
import os
import glob
import sys
import pdb
import ast
import re
import time
import shutil
import zipfile
import logging
import argparse
import subprocess
import importlib.util
import pandas as pd

from utils import *

log_file = 'autograder.log'
logging.basicConfig(filename=log_file, level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# CSV Files and Paths
grade_project           = "Project-0"
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

    name    = f"{row['Last Name']}{row['First Name']}".lower()
    name    = name.replace(' ', '').replace('-', '')
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

        test_pass, test_status, test_err, test_comments, test_script_err, test_results  = check_zip_contents(logger, sanity_script, zip_file, results)

        sanity_pass     = test_pass
        sanity_status   = test_status
        sanity_err      += test_err
        grade_comments  += test_comments
        results         = test_results

        if sanity_pass:

            print_and_log(logger, "Unzip submission and check folders/files: PASS")

            extracted_folder = f'extracted'
            extract_zip(logger, zip_file, extracted_folder)
            credentials_path = find_source_code_path(extracted_folder)

            print_and_log(logger, f"This is the submission file path: {credentials_path}")

            if not os.path.exists(credentials_path):
                print_and_log_error(logger, f"Credentials path does not exist: {credentials_path}")
                raise FileNotFoundError(f"Credentials path does not exist: {credentials_path}")

            # Check if credentials.txt exits
            credentials_txt_path = os.path.join(credentials_path, "credentials.txt")
            if not os.path.exists(credentials_txt_path):
                print_and_log_error(logger, f"credentials.txt not found in {credentials_path}")
                raise FileNotFoundError(f"credentials.txt not found in {credentials_path}")

            print_and_log(logger, f"Found credentials.txt  at {credentials_path}")
            cred_values = read_and_extract_credentials(logger,credentials_txt_path)

            try:
                # Test the project submission
                if (is_none_or_empty(cred_values[0]) == False and is_none_or_empty(cred_values[1]) == False):
                    aws_obj = aws_grader(logger, asuid, cred_values[0], cred_values[1])
                else:
                    print_and_log_error(logger, "Issue with credentials submitted. Points: [0/100]")
                    tc_1_pts = tc_2_pts = tc_3_pts = grade_points = 0
                    grade_comments += f"Issue with submitted credentials."
                    results.append({'Name': name, 'ASUID': asuid, 'Test-Sanity': sanity_status,
                                    'Test-1-score': tc_1_pts, 'Test-1-logs': grade_comments,
                                    'Test-2-score': tc_2_pts, 'Test-2-logs': grade_comments,
                                    'Test-3-score': tc_3_pts, 'Test-3-logs': grade_comments,
                                    'Total Grades':grade_points, 'Comments':grade_comments})
                    break

                try:
                    attached_policies = aws_obj.iam_client.list_attached_user_policies(UserName='cse546-AutoGrader',
                                                                                    MaxItems=100)
                    policy_names = [policy['PolicyName'] for policy in attached_policies['AttachedPolicies']]
                    print_and_log(logger, f"Following policies are attached with IAM user:cse546-AutoGrader: {policy_names}")

                    tc_1_pts, tc_1_comments, tc_2_pts, tc_2_comments, tc_3_pts, tc_3_comments = aws_obj.main(policy_names)
                    grade_points = tc_1_pts + tc_2_pts + tc_3_pts
                    if grade_points == 99.99: grade_points = 100

                    grade_comments += tc_1_comments
                    grade_comments += tc_2_comments
                    grade_comments += tc_3_comments

                    results.append({'Name': name, 'ASUID': asuid, 'Test-Sanity': sanity_status,
                                    'Test-1-score': tc_1_pts, 'Test-1-logs': tc_1_comments,
                                    'Test-2-score': tc_2_pts, 'Test-2-logs': tc_2_comments,
                                    'Test-3-score': tc_3_pts, 'Test-3-logs': tc_3_comments,
                                    'Total Grades':grade_points, 'Comments':grade_comments})
                except ClientError as e:

                    tc_1_pts = tc_2_pts = tc_3_pts = grade_points = 0
                    print_and_log_error(logger, f"Failed to fetch the attached polices. {e}")
                    print_and_log_error(logger, f"Total Grade Points: {grade_points}")
                    grade_comments += f"Failed to fetch attached policies. {e}"

                    results.append({'Name': name, 'ASUID': asuid, 'Test-Sanity': sanity_status,
                                    'Test-1-score': tc_1_pts, 'Test-1-logs': grade_comments,
                                    'Test-2-score': tc_2_pts, 'Test-2-logs': grade_comments,
                                    'Test-3-score': tc_3_pts, 'Test-3-logs': grade_comments,
                                    'Total Grades':grade_points, 'Comments':grade_comments})

            except subprocess.CalledProcessError as e:
                print_and_log_error(logger, "Error encountered while grading. Please inspect the autograder logs..")

            # Clean up: remove the extracted folder
            try:
                shutil.rmtree(extracted_folder)
                print_and_log(logger, f"Removed extracted folder: {extracted_folder}")
            except Exception as e:
                print_and_log_error(logger, f"Could not remove extracted folder {extracted_folder}: {e}")
        else:

            status = "Unzip submission and check folders/files: FAIL"
            print_and_log_error(logger, status)
            grade_comments += status

            results.append(
                    {'Name': name, 'ASUID': asuid, 'Test-Sanity': sanity_status,
                    'Test-1-score': status, 'Test-1-logs': status,
                    'Test-2-score': status, 'Test-2-logs': status,
                    'Test-3-score': status, 'Test-3-logs': status,
                    'Total Grades':grade_points, 'Comments':grade_comments})

            logger.handlers[0].flush()

    else:
        script_err          = 'Submission File (.zip) not found'
        print_and_log_error(logger, f"Submission File (.zip) not found for {asuid}")

        grade_comments      += "Submission File (.zip) not found. There is a possiblity that student has misspelled their name or asuid so please check if their submission exists and adheres to the project submission guidelines."
        results.append(
            {'Name': name, 'ASUID': asuid, 'Test-Sanity': "Not checked",
            'Test-1-score': script_err, 'Test-1-logs': script_err,
            'Test-2-score': script_err, 'Test-2-logs': script_err,
            'Test-3-score': script_err, 'Test-3-logs': script_err,
            'Total Grades':grade_points, 'Comments':grade_comments}
        )

    write_to_csv(results, grader_results_csv)

    # End timer
    end_time = time.time()

    # Calculate and print execution time
    execution_time = end_time - start_time
    print_and_log(logger, f"Execution Time for {last_name} {first_name} ASUID: {asuid}: {execution_time} seconds")
    print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.handlers[0].flush()

print_and_log(logger, f"Grading complete for {grade_project}. Check the {grader_results_csv} file.")
