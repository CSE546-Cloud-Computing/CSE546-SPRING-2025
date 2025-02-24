#!/usr/bin/python3

"""
File: grade_project0.py
Author: Kritshekhar Jha
Date: 2025-01-01
Description: Grading script for Project-0
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
from validate_permission_policies import *

parser = argparse.ArgumentParser(description='Upload images')
parser.add_argument('--img_folder', type=str, help='Path to the input images')
parser.add_argument('--pred_file', type=str, help='Classfication results file')
parser.add_argument('--num_requests', type=validate_num_requests, help='Number of Requests', default=100)

args            = parser.parse_args()
img_folder      = args.img_folder
pred_file       = args.pred_file
num_requests    = args.num_requests

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
grader_script           = f'{project_path}/grade_project1_p2.py'

print_and_log(logger, f'+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++')
print_and_log(logger, "- 1) Extract the credentials from the credentials.txt")
print_and_log(logger, "- 2) Execute the test cases as per the Grading Rubrics")
print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

print_and_log(logger, f'++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++')
print_and_log(logger, f"Project Path: {project_path}")
print_and_log(logger, f"Grade Project: {grade_project}")
print_and_log(logger, f"Class Roster: {roster_csv}")
print_and_log(logger, f"Zip folder path: {zip_folder_path}")
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
    #name    = f"{row['Last Name']}{row['First Name']}".lower()
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
        extracted_folder = f'extracted'
        del_directory(logger, extracted_folder)
        extract_zip(logger, zip_file, extracted_folder)

        credentials_txt_path = "extracted/credentials/credentials.txt"
        cred_values = read_and_extract_file(logger,credentials_txt_path)

        web_server_path  = "extracted/web-tier/server.py"
        web_server_exist = read_and_extract_file(logger,web_server_path)

        controller_path  = "extracted/web-tier/controller.py"
        controller_exist = read_and_extract_file(logger,controller_path)

        app_tier_path    = "extracted/app-tier/backend.py"
        app_tier_exist   = read_and_extract_file(logger,app_tier_path)

        if not cred_values or not web_server_exist or not controller_exist or not app_tier_exist:
            sanity_pass     = False
            test_pass       = False
            test_status     = "Fail"
            test_comments   = f"Sanity Test Failed: All expected files not found. Please check if the zip follows the correct structure as per the project document."
            test_err        = ""
            test_script_err = ""
            test_results    = []
        else:
            sanity_pass     = True
            test_pass       = True
            test_status     = "Pass"
            test_comments   = "Sanity Test Passed: All expected files found."
            test_err        = ""
            test_script_err = ""
            test_results    = []

        sanity_pass     = test_pass
        sanity_status   = test_status
        sanity_err      += test_err
        grade_comments  += test_comments
        results         = test_results

        if sanity_pass:

            sanity_comment = "Unzip submission and check folders/files: PASS"
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
                    iam_ro_access_flag, ec2_ro_access_flag, s3_full_access_flag, sqs_full_access_flag = iam_obj.validate_policies()

                    if (iam_ro_access_flag == False):
                        print_and_log(logger, "IAMReadOnlyAccess not attached.")

                    # STEP-4: Validate the billing alarm
                    cloudwatch_obj  = aws_cloudwatch(logger, cred_values[0], cred_values[1])
                    cloudwatch_obj.main()

                    # STEP-5: Execute test cases
                    aws_grader    = grader_project1(logger, asuid, cred_values[0], cred_values[1], ec2_ro_access_flag, s3_full_access_flag, sqs_full_access_flag)
                    ip_addr       = cred_values[2]
                    test_results  = aws_grader.main(num_requests, ip_addr, img_folder, pred_file)
                    grade_points  = test_results["grade_points"]

                    grade_comments += test_results["tc_2"][1]
                    grade_comments += test_results["tc_3"][1]

                    results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                            "Pass", "IAMReadOnlyAccess attached", test_results["tc_2"][0], test_results["tc_2"][1],
                                            test_results["tc_3"][0], test_results["tc_3"][1], grade_points, grade_comments)

                except (ClientError, Exception) as e:
                    print_and_log_error(logger, f"Failed to fetch the attached polices. {e}")
                    print_and_log_error(logger, f"Total Grade Points: {grade_points}")
                    grade_comments += f"Failed to fetch attached policies. {e}"
                    tc_2_pts = tc_3_pts = grade_points = 0
                    results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                                "Fail",   grade_comments, tc_2_pts, grade_comments,
                                                tc_3_pts, grade_comments, grade_points, grade_comments)

            except (subprocess.CalledProcessError,Exception) as e:
                print_and_log_error(logger, "Error encountered while grading. Please inspect the autograder logs..")

            # Clean up: remove the extracted folder
            del_directory(logger, extracted_folder)

        else:
            sanity_comment = f"Unzip submission and check folders/files: FAIL {test_comments}"
            grade_comments += sanity_comment
            tc_2_pts = tc_3_pts = grade_points = 0
            results = append_grade_remarks(results, name, asuid, sanity_status, sanity_comment,
                                                "Fail",   grade_comments, tc_2_pts, grade_comments,
                                                tc_3_pts, grade_comments, grade_points, grade_comments)
            logger.handlers[0].flush()
            del_directory(logger, extracted_folder)

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
    print_and_log(logger, f"Total time taken to grade for {last_name} {first_name} ASUID: {asuid}: {execution_time} seconds")
    print_and_log(logger, "++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    logger.handlers[0].flush()

print_and_log(logger, f"Grading complete for {grade_project}. Check the {grader_results_csv} file.")
