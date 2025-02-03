
__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

"""
File: grade_project1.py
Author: Kritshekhar Jha
Description: Grading script for Project-0
"""
import re
import os
import pdb
import json
import boto3
import httpx
import dotenv
import logging
import argparse
import subprocess
from botocore.exceptions import ClientError

WORKLOAD_TIMEOUT = 25

class grader_project1():
    def __init__(self, logger, asuid, access_keyId, access_key, ec2_ro_access_flag, s3_full_access_flag):

        self.iam_access_keyId       = access_keyId
        self.iam_secret_access_key  = access_key
        self.iam_session            = boto3.Session(aws_access_key_id = self.iam_access_keyId,
                                                    aws_secret_access_key = self.iam_secret_access_key)
        self.ec2_resources          = self.iam_session.resource('ec2', 'us-east-1')
        self.s3_resources           = self.iam_session.resource('s3', 'us-east-1')
        self.simpledb_client        = self.iam_session.client('sdb', 'us-east-1')
        self.logger                 = logger
        self.ec2_ro_access_flag     = ec2_ro_access_flag
        self.s3_full_access_flag    = s3_full_access_flag
        self.in_bucket_name         = f"{asuid}-in-bucket"
        self.simpledb_domain_name   = f"{asuid}-simpleDB"


    def print_and_log(self, message):
        print(message)
        self.logger.info(message)

    def print_and_log_error(self, message):
        print(message)
        self.logger.error(message)

    def get_tag(self, tags, key='Name'):

        if not tags:
            return 'None'
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return 'None'

    def validate_ec2_state(self):
        points_deducted = 0
        if self.ec2_ro_access_flag == True:
            self.print_and_log("[EC2-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM")
        else:
            comments = "[EC2-log] AmazonEC2ReadOnlyAccess policy NOT attached with grading IAM."
            self.print_and_log(comments)
        try:
            message = ""
            for instance in self.ec2_resources.instances.all():
                name = self.get_tag(instance.tags)
                if name == "web-instance":
                    message += "web-tier instance found."
                    state = instance.state['Name']
                    message += f" With state: {state}"
                    if state == "running":
                        self.web_tier_instanceId = instance.id
                        points_deducted = 0
                        comment = f"[EC2-log] EC2-state Pass. {message}.Points deducted: {points_deducted}"
                        self.print_and_log(comment)
                        return points_deducted, comment
                    else:
                        points_deducted = 33.33
                        comment = f"[EC2-log] EC2-state Fail. {message}. Points deducted: {points_deducted}"
                        self.print_and_log_error(comment)
                        return points_deducted, comment
            message += "web-tier Instance Not Found."
            points_deducted = 33.33
            comment = f"[EC2-log] EC2-state Fail. {message}. Points deducted: {points_deducted}"
            self.print_and_log_error(comment)
            return points_deducted, comment
        except ClientError as e:
            points_deducted = 33.33
            comments = f"[EC2-log] S3 validation failed {e}. Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def count_bucket_objects(self, bucket_name):
        bucket = self.s3_resources.Bucket(bucket_name)
        count  = 0
        for index in bucket.objects.all():
            count += 1
        return count

    def validate_s3_buckets(self):
        points_deducted = 0
        if self.s3_full_access_flag == True:
            self.print_and_log("[S3-log] AmazonS3FullAccess policy attached with grading IAM")
        else:
            comments = "[S3-log] AmazonS3FullAccess policy NOT attached with grading IAM"
            self.print_and_log(comments)

        try:
            self.print_and_log("[S3-log] - WARN: If there are objects in the S3 buckets; they will be deleted")
            self.print_and_log("[S3-log] ---------------------------------------------------------")

            bucket = self.s3_resources.Bucket(self.in_bucket_name)
            ip_obj_count  = 0
            for index in bucket.objects.all():
                ip_obj_count += 1

            if ip_obj_count:
                points_deducted = 33.33
                comments = f"[S3-log] S3 Bucket:{self.in_bucket_name} has {ip_obj_count} object(s). Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                self.empty_s3_bucket(self.in_bucket_name)
                return points_deducted, comments
            else:
                points_deducted = 0
                comments = f"[S3-log] S3 Bucket:{self.in_bucket_name} has {ip_obj_count} object(s). Points deducted:{points_deducted}"
                self.print_and_log(comments)
                return points_deducted, comments
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                points_deducted = 33.33
                comments = f"[S3-log] Bucket:{self.in_bucket_name} does not exist. Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                return points_deducted, comments
            else:
                points_deducted = 33.33
                comments = f"[S3-log] Bucket:{self.in_bucket_name} validation failed {e}. Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                return points_deducted, comments

    def validate_simpledb_domain(self):
        points_deducted = 0
        try:
            domains=self.simpledb_client.list_domains(MaxNumberOfDomains=100)
            available_domains = domains.get('DomainNames')
            if available_domains and self.simpledb_domain_name in available_domains:
                self.print_and_log(f"[DB-log] SimpleDB Domain: {self.simpledb_domain_name} exist")
                domain_metadata = self.simpledb_client.domain_metadata(DomainName=self.simpledb_domain_name)
                item_count      = domain_metadata.get('ItemCount')
                if item_count == 1000:
                    points_deducted = 0
                    comments = f"[DB-log] SimpleDB Domain: {self.simpledb_domain_name} exist with 1000 items. Points deducted:{points_deducted}"
                    self.print_and_log(comments)
                    return points_deducted, comments
                else:
                    points_deducted = 33.33
                    comments = f"[DB-log] SimpleDB Domain: {self.simpledb_domain_name} exist with {item_count}/1000 items. Points deducted:{points_deducted}"
                    self.print_and_log_error(comments)
                    return points_deducted, comments
            else:
                points_deducted = 33.33
                comments = f"[DB-log] SimpleDB Domain: {self.simpledb_domain_name} does not exist. Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                return points_deducted, comments
        except ClientError as e:
            points_deducted = 33.33
            comments = f"[DB-log] SimpleDB Domain validation failed {e}. Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def parse_workload_stats(self, stdout):
        stats = {}
        stats["total_requests"]      = int(re.search(r"Total number of requests: (\d+)", stdout).group(1))
        stats["completed_requests"]  = int(re.search(r"Total number of requests completed successfully: (\d+)", stdout).group(1))
        stats["failed_requests"]     = int(re.search(r"Total number of failed requests: (\d+)", stdout).group(1))
        stats["correct_predictions"] = int(re.search(r"Total number of correct predictions : (\d+)", stdout).group(1))
        stats["wrong_predictions"]   = int(re.search(r"Total number of wrong predictions: (\d+)", stdout).group(1))
        stats["test_duration"]       = float(re.search(r"Total Test Duration:\s*([0-9]+\.[0-9]+)", stdout).group(1))
        return stats

    def empty_s3_bucket(self, bucket_name):
        try:
            bucket = self.s3_resources.Bucket(bucket_name)
            response = bucket.objects.all().delete()
            if response and isinstance(response, list) and response:
                errors = response[0].get('Errors', [])
                if errors:
                    first_error = errors[0]
                    self.print_and_log(f"[S3-log] Emptying the bucket failed. Error Details: {errors}")
                else:
                    self.print_and_log(f"[S3-log] Bucket:{bucket_name} is now EMPTY !!")
            else:
                self.print_and_log(f"[S3-log] Bucket deletion response is empty or None. No deletion occurred.")
        except ClientError as e:
            comments = f"[S3-log] Failed to empty the S3 bucket:{bucket_name}. Reason: {e}"
            self.print_and_log_error(comments)

    def run_workload_generator(self, num_req, ip_addr, img_folder, pred_file):
        wkld_gen_cmd = [
                "python3",
                "workload_generator.py",
                f"--num_request={num_req}",
                f"--ip_addr={ip_addr}",
                f"--image_folder={img_folder}",
                f"--prediction_file={pred_file}",]
        result          = subprocess.run(wkld_gen_cmd, capture_output=True, text=True, check=True, timeout=WORKLOAD_TIMEOUT)
        stdout_output   = result.stdout
        stderr_output   = result.stderr
        self.print_and_log(f"{stdout_output}")
        stats = self.parse_workload_stats(stdout_output)
        return stats

    def validate_s3_bucket(self, num_req, stats):
        total_s3_count_score   = 20
        s3_bucket_count     = self.count_bucket_objects(self.in_bucket_name)
        points_per_s3_entry = total_s3_count_score / num_req
        test_case_points    = s3_bucket_count* points_per_s3_entry
        test_case_points    = min(test_case_points, total_s3_count_score)
        test_case_points    = round(test_case_points, 2)
        comments = f"[Test-Case-3-log] {s3_bucket_count}/{num_req} entries in S3 bucket:{self.in_bucket_name}.Points:[{test_case_points}/{total_s3_count_score}]"
        self.empty_s3_bucket(self.in_bucket_name)
        self.print_and_log(comments)
        return test_case_points, comments

    def validate_completeness(self, num_req, stats):
        total_completion_score = 20
        points_per_request = total_completion_score / num_req
        completed_requests = stats.get("completed_requests", 0)
        test_case_points   = completed_requests * points_per_request
        test_case_points   = min(test_case_points, total_completion_score)
        test_case_points   = round(test_case_points, 2)
        comments = f"[Test-Case-3-log] {completed_requests}/{num_req} completed successfully.Points:[{test_case_points}/{total_completion_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def validate_correctness(self, num_req, stats):
        total_correctness_score = 20
        points_per_request = total_correctness_score / num_req
        correct_prediction = stats.get("correct_predictions", 0)
        test_case_points   = correct_prediction * points_per_request
        test_case_points   = min(test_case_points, total_correctness_score)
        test_case_points   = round(test_case_points, 2)
        comments = f"[Test-Case-3-log] {correct_prediction}/{num_req} correct predictions.Points:[{test_case_points}/{total_correctness_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def validate_latency(self, num_req, stats):
        total_test_score = 40
        latency          = stats.get("test_duration", 0)
        if latency <= 10:
            # The total test duration for 1000 requests is less than 10 sec (40)
            points_deducted = 0
            comments = f"[Test-Case-3-log] Test Latency: {latency} sec. `latency<=10`."
        elif (latency > 10 and latency <= 15):
            # The total test duration for 1000 requests is between 10 sec - 15 sec (20)
            points_deducted = 20
            comments = f"[Test-Case-3-log] Test Latency: {latency} sec. `latency>10 and latency<=15`."
        elif (latency > 15 and latency <= 20):
            # The test duration for 1000 requests is between 15 seconds - 20 seconds (10)
            points_deducted = 30
            comments = f"[Test-Case-3-log] Test Latency: {latency} sec. `latency>15 and latency<=20`."
        else:
            #The total test duration for 1000 requests is greater than 20 seconds (0)
            points_deducted = 40
            comments = f"[Test-Case-3-log] Test Latency: {latency} sec. `latency>20`."

        test_case_points = total_test_score - points_deducted
        test_case_points = max(test_case_points, 0)
        test_case_points = round(test_case_points, 2)
        comments += f"Points:[{test_case_points}/{total_test_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def evaluate_iaas(self, num_req, ip_addr, img_folder, pred_file):

        try:
            if os.path.exists(img_folder) and os.path.exists(pred_file):

                stats = self.run_workload_generator(num_req, ip_addr, img_folder, pred_file)

                s3_score, s3_log                     = self.validate_s3_bucket(num_req, stats)
                completeness_score, completeness_log = self.validate_completeness(num_req, stats)
                correctness_score, correctness_log   = self.validate_correctness(num_req, stats)
                latency_score, latency_log           = self.validate_latency(num_req, stats)

                test_case_points = s3_score + completeness_score + correctness_score + latency_score
                comments  = s3_log
                comments += completeness_log
                comments += correctness_log
                comments += latency_log
                return test_case_points, comments
            else:
                comments = f"Issue with the arguments.Check if the input arguments are correct.\nimg_folder:{img_folder} pred_file:{pred_file}"
                self.print_and_log_error(f"[Test-Case-log] Evaluate IaaS failed. {comments}")
                return 0, comments
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            comments = ""
            self.print_and_log_error(f"[Test-Case-log] Workload generator failed with return code {e}")
            self.print_and_log_error(f"[Test-Case-log] Standard output: {e.stdout}")
            self.print_and_log_error(f"[Test-Case-log] Standard error: {e.stderr}")
            comments = f"[Test-Case-log] Error: {e.stdout} + {e.stderr}"
            return 0, comments

    def validate_initial_states(self):
        ec2_pts_deducted, ec2_logs = self.validate_ec2_state()
        s3_pts_deducted, s3_logs   = self.validate_s3_buckets()
        simpledb_pts_deducted, simpledb_logs = self.validate_simpledb_domain()

        total_points_deducted = ec2_pts_deducted + s3_pts_deducted + simpledb_pts_deducted
        comments = ec2_logs
        comments += s3_logs
        comments += simpledb_logs

        return (-1*total_points_deducted), comments

    def main(self, ip_addr, img_folder, pred_file):
        test_results = {}

        self.print_and_log("-------------- CSE546 Cloud Computing Grading Console -----------")
        self.print_and_log(f"IAM ACESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(f"IAM SECRET ACCESS KEY: {self.iam_secret_access_key}")
        self.print_and_log(f"Web-Instance IP Address: {ip_addr}")
        self.print_and_log("-----------------------------------------------------------------")

        self.print_and_log("----------------- Executing Test-Case:2 ----------------")
        test_results["tc_2"] = self.validate_initial_states()
        self.print_and_log("----------------- Executing Test-Case:3 ----------------")
        test_results["tc_3"] = self.evaluate_iaas(1000, ip_addr, img_folder, pred_file)

        grade_points = sum(result[0] for result in test_results.values())
        if grade_points == 99.99: grade_points = 100
        if grade_points < 0: grade_points = 0
        self.print_and_log(f"Total Grade Points: {grade_points}")
        test_results["grade_points"] = grade_points

        return test_results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload images')
    parser.add_argument('--access_keyId', type=str, help='ACCCESS KEY ID of the grading IAM user')
    parser.add_argument('--access_key', type=str, help='SECRET ACCCESS KEY of the grading IAM user')
    parser.add_argument('--asuid', type=str, help='ASUID of the student')

    log_file = 'autograder.log'
    logging.basicConfig(filename=log_file, level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args = parser.parse_args()

    access_keyId = args.access_keyId
    access_key   = args.access_key
    asuid        = args.asuid
    aws_obj = grader_project1(logger, asuid, access_keyId, access_key, True, True)
