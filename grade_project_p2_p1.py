"""
File: grade_project_p1_p1.py
Author: Kritshekhar Jha
Description: Grading script for Project-2
"""
import re
import os
import pdb
import time
import json
import queue
import boto3
import httpx
import dotenv
import logging
import argparse
import textwrap
import threading
import subprocess
from botocore.exceptions import ClientError

WORKLOAD_TIMEOUT = 420

class grader_project2():
    def __init__(self, logger, asuid, access_keyId, access_key, sqs_full_access_flag, lambda_ro_access_flag):

        self.iam_access_keyId       = access_keyId
        self.iam_secret_access_key  = access_key
        self.iam_session            = boto3.Session(aws_access_key_id = self.iam_access_keyId,
                                                    aws_secret_access_key = self.iam_secret_access_key)
        self.sqs_resources          = self.iam_session.resource('sqs',  'us-east-1')
        self.sqs_client             = self.iam_session.client('sqs',    'us-east-1')
        self.lambda_function        = self.iam_session.client('lambda', 'us-east-1')
        self.logger                 = logger
        self.sqs_full_access_flag   = sqs_full_access_flag
        self.lambda_ro_access_flg   = lambda_ro_access_flag
        self.asuid                  = asuid
        self.req_sqs_name           = f"{asuid}-req-queue"
        self.resp_sqs_name          = f"{asuid}-resp-queue"

    def print_and_log(self, message):
        print(message)
        self.logger.info(message)

    def print_and_log_warn(self, message):
        print(message)
        self.logger.warn(message)

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

    def validate_lambda_triggers(self):
        comments                     = ""
        points_deducted              = 0
        trigger_403_pts_deduction    = 100
        face_recognition_lambda_name = "face-recognition"

        try:
            response = self.lambda_function.list_event_source_mappings(FunctionName=face_recognition_lambda_name)
            for mapping in response.get("EventSourceMappings", []):
                event_source_arn = mapping.get("EventSourceArn", "")
                if event_source_arn.startswith("arn:aws:sqs"):
                    comments +=  f"[Lambda-Trigger-log] SQS Trigger Found with Lambda func:{face_recognition_lambda_name}: {event_source_arn}\n"
                else:
                    comments +=  f"[Lambda-Trigger-Log] SQS Trigger NOT Found with Lambda func:{face_recognition_lambda_name}: {event_source_arn}\n"
                    points_deducted += trigger_403_pts_deduction

            comments += f"[Lambda-Trigger-log] Points deducted:{points_deducted}"
            self.print_and_log(comments)
            self.print_and_log("[Lambda-Trigger-log] ---------------------------------------------------------")
            return points_deducted, comments

        except self.lambda_function.exceptions.ResourceNotFoundException as e:
            points_deducted += trigger_403_pts_deduction
            comments = f"[Lambda-Trigger-log] Lambda trigger validation failed {ex}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def validate_lambda_exists(self):
        comments                    = ""
        points_deducted             = 0
        lambda_403_pts_deduction    = 100

        face_detection_lambda_name   = "face-detection"
        face_recognition_lambda_name = "face-recognition"

        try:
            fn_response    = self.lambda_function.list_functions()
            function_names = [func['FunctionName'] for func in fn_response.get('Functions', [])]

            fd_response = self.lambda_function.get_function(FunctionName=face_detection_lambda_name)
            fr_response = self.lambda_function.get_function(FunctionName=face_recognition_lambda_name)

            if face_detection_lambda_name in function_names:
                comments += f"[Lambda-log] The function: {face_detection_lambda_name} exists\n"
            else:
                comments += f"[Lambda-log] The function: {face_detection_lambda_name} does not exists\n"
                points_deducted += lambda_403_pts_deduction

            if face_recognition_lambda_name in function_names:
                comments += f"[Lambda-log] The function: {face_recognition_lambda_name} exists.\n"
            else:
                comments += f"[Lambda-log] The function: {face_recognition_lambda_name} does not exists.\n"
                points_deducted += lambda_403_pts_deduction

            comments += f"[Lambda-log] Points deducted:{points_deducted}"
            self.print_and_log(comments)
            self.print_and_log("[Lambda-log] ---------------------------------------------------------")
            return points_deducted, comments

        except self.lambda_function.exceptions.ResourceNotFoundException as e:
            points_deducted += lambda_403_pts_deduction
            comments = f"[Lambda-log] Lambda validation failed {e}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def check_sqs_queue_type(self, sqs_resp_url):
        response = self.sqs_client.get_queue_attributes(
                QueueUrl=sqs_resp_url,
                AttributeNames=["FifoQueue"]
                )
        if response.get("Attributes", {}).get("FifoQueue") == "true":
            self.req_sqs_name           = f"{self.asuid}-req-queue.fifo"
            self.resp_sqs_name          = f"{self.asuid}-resp-queue.fifo"
        else:
            self.req_sqs_name           = f"{self.asuid}-req-queue"
            self.resp_sqs_name          = f"{self.asuid}-resp-queue"

    def validate_sqs_queues(self, sqs_resp_url):
        points_deducted             = 0
        q_msg_count_pts_deduction   = 10

        #self.check_sqs_queue_type(sqs_resp_url)

        self.print_and_log("[SQS-log] The expectation is that both the Request and Response SQS should exist and be EMPTY")
        self.print_and_log("[SQS-log] - WARN: This will purge any messages available in the SQS")
        self.print_and_log("[SQS-log] ---------------------------------------------------------")

        '''
        if self.sqs_full_access_flag == True:
            self.print_and_log("[SQS-log] AmazonSQSFullAccess policy attached with grading IAM")
        else:
            comments = "[SQS-log] AmazonSQSFullAccess policy NOT attached with grading IAM"
            self.print_and_log(comments)
        '''

        try:
            #req_sqs  = self.sqs_resources.get_queue_by_name(QueueName=self.req_sqs_name)
            #resp_sqs = self.sqs_resources.get_queue_by_name(QueueName=self.resp_sqs_name)

            ip_queue_requests = int(self.sqs_client.get_queue_attributes(QueueUrl=self.req_sqs_name, AttributeNames=['ApproximateNumberOfMessages'])['Attributes']['ApproximateNumberOfMessages'])
            op_queue_response = int(self.sqs_client.get_queue_attributes(QueueUrl=self.resp_sqs_name, AttributeNames=['ApproximateNumberOfMessages'])['Attributes']['ApproximateNumberOfMessages'])

            comments = f"[SQS-log] SQS Request Queue:{self.req_sqs_name} has {ip_queue_requests} pending messages.\n"
            comments += f"[SQS-log] SQS Response Queue:{self.resp_sqs_name} has {op_queue_response} pending messages.\n"

            if ip_queue_requests or op_queue_response:

                points_deducted += q_msg_count_pts_deduction

                if ip_queue_requests:
                    self.print_and_log_warn(f"[SQS-log] Purging the Requeust SQS: {self.req_sqs_name}. Waiting 60 seconds ...")
                    self.sqs_client.purge_queue(QueueUrl=self.req_sqs_name)
                    time.sleep(60)

                if op_queue_response:
                    self.print_and_log_warn(f"[SQS-log] Purging the Response SQS: {self.resp_sqs_name}. Waiting 60 seconds ...")
                    self.sqs_client.purge_queue(QueueUrl=self.resp_sqs_name)
                    time.sleep(60)

            comments += f"[SQS-log] Points deducted:{points_deducted}"
            self.print_and_log(comments)
            return points_deducted, comments

        except Exception as ex:
            points_deducted += q_msg_count_pts_deduction
            comments = f"[SQS-log] SQS validation failed {ex}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments


    def parse_workload_stats(self, stdout):
        stats = {}
        stats["total_requests"]      = int(re.search(r"Total number of requests: (\d+)", stdout).group(1))
        stats["completed_requests"]  = int(re.search(r"Total number of requests completed successfully: (\d+)", stdout).group(1))
        stats["failed_requests"]     = int(re.search(r"Total number of failed requests: (\d+)", stdout).group(1))
        stats["correct_predictions"] = int(re.search(r"Total number of correct predictions : (\d+)", stdout).group(1))
        stats["wrong_predictions"]   = int(re.search(r"Total number of wrong predictions: (\d+)", stdout).group(1))
        stats["total_test_duration"] = float(re.search(r"Total test duration:\s*([0-9]+\.[0-9]+)", stdout).group(1))
        #stats["test_latency"]        = float(re.search(r"Test Latency:\s*([0-9]+\.[0-9]+)", stdout).group(1))
        return stats

    def run_workload_generator(self, access_keyID, access_key, num_req, lambda_url, response_queue_url, img_folder, pred_file):
        wkld_gen_cmd = [
                "python3",
                "workload_generator.py",
                f"--access_keyID={access_keyID}",
                f"--access_key={access_key}",
                f"--num_request={num_req}",
                f"--lambda_url={lambda_url}",
                f"--response_queue_url={response_queue_url}",
                f"--image_folder={img_folder}",
                f"--prediction_file={pred_file}",]
        result          = subprocess.run(wkld_gen_cmd, capture_output=True, text=True, check=True, timeout=WORKLOAD_TIMEOUT)
        stdout_output   = result.stdout
        stderr_output   = result.stderr
        self.print_and_log(f"{stdout_output}")
        time.sleep(2)
        stats = self.parse_workload_stats(stdout_output)
        return stats

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
        total_test_score    = 60
        completed_requests  = stats.get("completed_requests", 0)
        latency             = stats.get("total_test_duration", 0)
        comments            = ""

        if completed_requests == num_req:
            avg_latency         = latency / completed_requests
            if avg_latency > 0:
                deductions = [(3, 0, "avg latency<3s"),
                        (4, 20, "avg latency>=3s and avg latency<4s"),
                        (5, 40, "avg latency>=4s and avg latency<5"),
                        (float('inf'), 60, "avg latency>5")]

                for threshold, points_deducted, condition in deductions:
                    if avg_latency < threshold:
                        break

                comments = f"[Test-Case-3-log] Test Average Latency: {avg_latency} sec. `{condition}`."
            else:
                points_deducted = total_test_score
                comments = f"[Test-Case-3-log] Test Average Latency: {avg_latency} sec.."
        else:
            comments += f"[Test-Case-3-log] Only {completed_requests}/{num_req} completed successfully. Invalid scenario for latency rubric."
            points_deducted = total_test_score

        test_case_points = total_test_score - points_deducted
        test_case_points = max(test_case_points, 0)
        test_case_points = round(test_case_points, 2)
        comments += f"Points:[{test_case_points}/{total_test_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def evaluate_paas(self, num_req, lambda_url, sqs_resp_url, img_folder, pred_file):

        self.num_req        = num_req
        test_case_points    = 0
        stats               = {}

        try:
            stats = self.run_workload_generator(self.iam_access_keyId, self.iam_secret_access_key, num_req, lambda_url, sqs_resp_url, img_folder, pred_file)

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            comments = ""
            self.print_and_log_error(f"[Test-Case-log] Workload generator failed with return code {e}")
            self.print_and_log_error(f"[Test-Case-log] Standard output: {e.stdout}")
            self.print_and_log_error(f"[Test-Case-log] Standard error: {e.stderr}")
            comments = f"[Test-Case-log] Error: {e.stdout} + {e.stderr}"
            return 0, comments
        finally:
            completeness_score, completeness_log = self.validate_completeness(num_req, stats)
            correctness_score, correctness_log   = self.validate_correctness(num_req, stats)
            latency_score, latency_log           = self.validate_latency(num_req, stats)
            self.print_and_log("[Test-Case-3-log] ---------------------------------------------------------")

            test_case_points += completeness_score + correctness_score + latency_score
            comments  = completeness_log
            comments += correctness_log
            comments += latency_log
            return test_case_points, comments

    def validate_initial_states(self, sqs_resp_url):
        lambda_pts_deducted, lambda_logs                = self.validate_lambda_exists()
        lambda_triggr_pts_deducted, lambda_trigger_logs = self.validate_lambda_triggers()
        sqs_pts_deducted, sqs_logs                      = self.validate_sqs_queues(sqs_resp_url)
        total_points_deducted                           = lambda_pts_deducted + lambda_triggr_pts_deducted  + sqs_pts_deducted

        comments                                        = lambda_logs
        comments                                       += lambda_trigger_logs
        comments                                       += sqs_logs
        return (-1*total_points_deducted), comments

    def main(self, num_req, lambda_url, sqs_resp_url, img_folder, pred_file):
        test_results = {}

        self.print_and_log("-------------- CSE546 Cloud Computing Grading Console -----------")
        self.print_and_log(f"IAM ACCESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(f"IAM SECRET ACCESS KEY: {self.iam_secret_access_key}")
        self.print_and_log(f"Face detection Lambda Function URL: {lambda_url}")
        self.print_and_log(f"SQS Response Queue URL: {sqs_resp_url}")
        self.print_and_log("-----------------------------------------------------------------")

        self.print_and_log("----------------- Executing Test-Case:1 ----------------")
        test_results["tc_2"] = self.validate_initial_states(sqs_resp_url)
        self.print_and_log("----------------- Executing Test-Case:2 ----------------")
        test_results["tc_3"] = self.evaluate_paas(num_req, lambda_url, sqs_resp_url, img_folder, pred_file)

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
    aws_obj = grader_project1(logger, asuid, access_keyId, access_key, True, True, True)
