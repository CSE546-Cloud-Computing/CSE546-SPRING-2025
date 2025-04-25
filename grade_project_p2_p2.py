__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

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
    def __init__(self, logger, asuid, access_keyId, access_key):

        self.iam_access_keyId       = access_keyId
        self.iam_secret_access_key  = access_key
        self.iam_session            = boto3.Session(aws_access_key_id = self.iam_access_keyId,
                                                    aws_secret_access_key = self.iam_secret_access_key)
        self.ec2_resources          = self.iam_session.resource('ec2', 'us-east-1')
        self.sqs_resources          = self.iam_session.resource('sqs',  'us-east-1')
        self.sqs_client             = self.iam_session.client('sqs',    'us-east-1')
        self.lambda_function        = self.iam_session.client('lambda', 'us-east-1')
        self.gg_client              = self.iam_session.client('greengrassv2', 'us-east-1')
        self.iot_client             = self.iam_session.client('iot', 'us-east-1')
        #self.gg_client              = boto3.client('greengrassv2', 'us-east-1')
        #self.iot_client             = boto3.client('iot', 'us-east-1')
        self.logger                 = logger
        self.asuid                  = asuid
        self.req_sqs_name           = f"{asuid}-req-queue"
        self.resp_sqs_name          = f"{asuid}-resp-queue"
        self.iot_thing_name         = f"{asuid}-IoTThing"
        self.mqtt_topic             = f"clients/{asuid}-IoTThing"
        self.iot_core_tag           = f"IoT-Greengrass-Core"
        self.iot_client_tag         = f"IoT-Greengrass-Client"

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

    def look_up_iot_components(self):

        status   = False
        cores    = self.gg_client.list_core_devices()
        comments = ""
        target_components = ['com.clientdevices.FaceDetection']

        try:

            for core in cores['coreDevices']:
                if core['coreDeviceThingName'] is not None:

                    coreDeviceThingName = core['coreDeviceThingName']
                    core_device_status  = core['status']

                    comment = f"[IoT-log] Found a IoT Core Device: {coreDeviceThingName} with state {core_device_status}."
                    self.print_and_log(comment)

                    if core_device_status != 'HEALTHY':
                        status = False
                        continue

                    components = self.gg_client.list_installed_components(coreDeviceThingName=coreDeviceThingName)['installedComponents']

                    #comment = f"[IoT-log] IoT Core Device: {coreDeviceThingName} have the following installed components {components}."
                    #self.print_and_log(comment)

                    if components :
                        for comp in components:
                            if comp['componentName'] in target_components:
                                if comp['lifecycleState'] == 'RUNNING':
                                    comment += f"[IoT-log] Found a component {comp['componentName']} in RUNNING state.\n"
                                    status  = True
                                    self.print_and_log(f"[IoT-log] Found a component {comp['componentName']} in RUNNING state.")
                                    return status, core, coreDeviceThingName, comments
                                else:
                                    status  = False
                                    comment += f"[IoT-log] Found a component {comp['componentName']} in {comp['lifecycleState']} state on core device: {coreDeviceThingName}.\n"
                                    self.print_and_log_error(f"[IoT-log] Found a component {comp['componentName']} in {comp['lifecycleState']} state on core device: {coreDeviceThingName}.")
                    else:
                        comments += f"[IoT-log] No components installed on the core device: {coreDeviceThingName}\n"
                        self.print_and_log(f"[IoT-log] No components installed on the core device: {coreDeviceThingName}")

            return status, None, None, comments
        except (ClientError, Exception) as e:
            status          = False
            comments        += f"[IoT-log] IoT Greengrass core face detection component validation failed {e}"
            self.print_and_log_error(f"[IoT-log] IoT Greengrass core face detection component validation failed {e}")
            return status, None, None, comments

    def validate_iot_core(self):
        points_deducted     = 0

        try:
            status, iot_core, core_dev_thing_name, core_comments = self.look_up_iot_components()
            if status:
                thing_details   = self.iot_client.describe_thing(thingName=core_dev_thing_name)
                response        = self.iot_client.list_things()

                if any(thing['thingName'] == self.iot_thing_name for thing in response.get('things', [])):
                    points_deducted     = 0
                    comments = f"[IoT-log] {self.iot_thing_name} found. Points deducted: {points_deducted}"
                    self.print_and_log(comments)
                    core_comments += comments
                    return points_deducted, core_comments

                else:
                    points_deducted = 100
                    comments = f"[IoT-log] {self.iot_thing_name} NOT found. Points deducted: {points_deducted}"
                    self.print_and_log(comments)
                    core_comments += comments
                    return points_deducted, core_comments
            else:
                points_deducted = 100
                comments        = f"[IoT-log] IoT Greengrass core face detection component validation failed.Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                core_comments += comments
                return points_deducted, core_comments

        except (ClientError, Exception) as e:
            points_deducted = 100
            comments        = f"[IoT-log] IoT Greengrass core face detection component validation failed {e}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            core_comments += comments
            return points_deducted, core_comments

    def get_instance_details(self, tag, state):
        instances = self.ec2_resources.instances.filter(
                Filters=[
                    {'Name': 'tag:Name', 'Values': [tag+"*"]},
                    {'Name': 'instance-state-name', 'Values': [state]}
                    ]
                )
        return len(list(instances))

    def validate_ec2_state(self):
        points_deducted = 0

        try:
            iot_core_instance   = self.get_instance_details(self.iot_core_tag, 'running')
            iot_client_instance = self.get_instance_details(self.iot_client_tag, 'running')
            #self.print_and_log(f"[EC2-log] Found {iot_core_instance} IoT Greengrass Core instances ({self.iot_core_tag}) in running state.")
            #self.print_and_log(f"[EC2-log] Found {iot_client_instance} IoT Greengrass Client instances ({self.iot_client_tag}) in running state")
            message = f"Found {iot_core_instance} IoT-Greengrass-Core instances instance in running state. Found {iot_client_instance} IoT-Greengrass-Client instance in running state"

            if not iot_core_instance:
                points_deducted = 100
                comment         = f"[EC2-log] IoT Greengrass Core state validation failed. {message}.Points deducted: {points_deducted}"
                self.print_and_log_error(comment)
                return points_deducted, comment

            if not iot_client_instance:
                points_deducted = 100
                comment         = f"[EC2-log] IoT Greengrass Client validation failed. {message}.Points deducted: {points_deducted}"
                self.print_and_log_error(comment)
                return points_deducted, comment

            points_deducted = 0
            comment         = f"[EC2-log] IoT Greengrass Core and client validation Pass. {message}.Points deducted: {points_deducted}"
            self.print_and_log(comment)
            return points_deducted, comment

        except (ClientError, Exception) as e:
            points_deducted = 100
            comments        = f"[EC2-log] IoT Greengrass core and client validation failed {e}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def validate_lambda_exists(self):
        comments                    = ""
        points_deducted             = 0
        lambda_403_pts_deduction    = 100

        face_recognition_lambda_name = "face-recognition"

        try:
            fn_response    = self.lambda_function.list_functions()
            function_names = [func['FunctionName'] for func in fn_response.get('Functions', [])]

            fr_response = self.lambda_function.get_function(FunctionName=face_recognition_lambda_name)

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

        try:
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
        return stats

    def init_workload_generator(self, asuid, ip_addr, pem_file_path, num_req, response_queue_url, img_folder, pred_file):
        wkld_gen_cmd = [
                "python3",
                "init_workload.py",
                f"--asu_id={asuid}",
                f"--ip_addr={ip_addr}",
                f"--pem={pem_file_path}",
                f"--max_pub_ops={num_req}",
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

    def validate_latency(self, num_req, stats, bonus_rubrics):
        total_test_score    = 60
        completed_requests  = stats.get("completed_requests", 0)
        latency             = stats.get("total_test_duration", 0)
        comments            = ""

        if completed_requests == num_req:
            avg_latency         = latency / completed_requests
            if avg_latency > 0:

                if bonus_rubrics == False:
                    total_test_score    = 60
                    deductions = [(2.5, 0, "avg latency<2.5s"),
                            (3.5, 20, "avg latency>=2.5s and avg latency<3.5s"),
                            (4.5, 40, "avg latency>=3.5s and avg latency<4.5"),
                            (float('inf'), 60, "avg latency>4.5")]
                else:
                    total_test_score    = 80
                    deductions = [(1.5, 0, "avg latency<1.5s"),
                            (2.5, 20, "avg latency>=1.5s and avg latency<2.5s"),
                            (3.5, 40, "avg latency>=2.5s and avg latency<3.5"),
                            (float('inf'), 80, "avg latency>3.5")]


                for threshold, points_deducted, condition in deductions:
                    if avg_latency < threshold:
                        break

                if bonus_rubrics == False:
                    comments += f"[Test-Case-3-log] Test Average Latency: {avg_latency} sec. `{condition}`."
                else:
                    comments += f"[Test-Case-3-log] Bonus rubrics enabled. Test Average Latency: {avg_latency} sec. `{condition}`."
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

    def evaluate_paas(self, asuid, ip_addr, pem_file_path, num_req, sqs_resp_url, img_folder, pred_file, use_bonus_rubrics):

        self.num_req        = num_req
        test_case_points    = 0
        stats               = {}

        try:
            stats = self.init_workload_generator(asuid, ip_addr, pem_file_path, num_req, sqs_resp_url, img_folder, pred_file)

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
            latency_score, latency_log           = self.validate_latency(num_req, stats, use_bonus_rubrics)
            self.print_and_log("[Test-Case-3-log] ---------------------------------------------------------")

            test_case_points += completeness_score + correctness_score + latency_score
            comments  = completeness_log
            comments += correctness_log
            comments += latency_log
            return test_case_points, comments

    def validate_initial_states(self, sqs_resp_url):

        ec2_pts_deducted, ec2_logs          = self.validate_ec2_state()
        iot_pts_deducted, iot_logs          = self.validate_iot_core()
        lambda_pts_deducted, lambda_logs    = self.validate_lambda_exists()
        sqs_pts_deducted, sqs_logs          = self.validate_sqs_queues(sqs_resp_url)
        total_points_deducted               = ec2_pts_deducted + iot_pts_deducted + lambda_pts_deducted + sqs_pts_deducted

        comments                            = ec2_logs
        comments                            += iot_logs
        comments                            += lambda_logs
        comments                            += sqs_logs
        return (-1*total_points_deducted), comments

    def main(self, asuid, num_req, pem_file_path, ip_addr, sqs_resp_url, img_folder, pred_file, bonus_rubrics):
        test_results = {}

        self.print_and_log("-------------- CSE546 Cloud Computing Grading Console -----------")
        self.print_and_log(f"IAM ACCESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(f"IAM SECRET ACCESS KEY: {self.iam_secret_access_key}")
        self.print_and_log(f"Elastic IPv4 address of IoT-Greengrass-Client :{ip_addr}")
        self.print_and_log(f"SQS Response Queue URL: {sqs_resp_url}")
        self.print_and_log("-----------------------------------------------------------------")

        self.print_and_log("----------------- Executing Test-Case:1 ----------------")
        test_results["tc_2"] = self.validate_initial_states(sqs_resp_url)
        self.print_and_log("----------------- Executing Test-Case:2 ----------------")
        test_results["tc_3"] = self.evaluate_paas(asuid, ip_addr, pem_file_path, num_req, sqs_resp_url, img_folder, pred_file, bonus_rubrics)

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
