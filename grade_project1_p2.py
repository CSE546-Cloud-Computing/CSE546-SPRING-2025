"""
File: grade_project1.py
Author: Kritshekhar Jha
Description: Grading script for Project-1
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

class grader_project1():
    def __init__(self, logger, asuid, access_keyId, access_key, ec2_ro_access_flag, s3_full_access_flag, sqs_full_access_flag):

        self.iam_access_keyId       = access_keyId
        self.iam_secret_access_key  = access_key
        self.iam_session            = boto3.Session(aws_access_key_id = self.iam_access_keyId,
                                                    aws_secret_access_key = self.iam_secret_access_key)
        self.ec2_resources          = self.iam_session.resource('ec2', 'us-east-1')
        self.s3_resources           = self.iam_session.resource('s3', 'us-east-1')
        self.simpledb_client        = self.iam_session.client('sdb', 'us-east-1')
        self.sqs_resources          = self.iam_session.resource('sqs', 'us-east-1')
        self.sqs_client             = self.iam_session.client('sqs', 'us-east-1')
        self.logger                 = logger
        self.ec2_ro_access_flag     = ec2_ro_access_flag
        self.s3_full_access_flag    = s3_full_access_flag
        self.sqs_full_access_flag   = sqs_full_access_flag
        self.in_bucket_name         = f"{asuid}-in-bucket"
        self.out_bucket_name        = f"{asuid}-out-bucket"
        self.simpledb_domain_name   = f"{asuid}-simpleDB"
        self.req_sqs_name           = f"{asuid}-req-queue"
        self.resp_sqs_name          = f"{asuid}-resp-queue"
        self.web_tier_tag           = f"web-instance"
        self.app_tier_tag           = f"app-tier-instance"
        self.max_ec2_instances      = 15

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

    def beautify_headers(self):

        column1 = " # of messages in SQS Request Queue "
        column2 = " # of messages in SQS Response Queue "
        column3 = " # of app-tier EC2 instances in running state "
        column4 = " # of objects in S3 Input Bucket "
        column5 = " # of objects in S3 Output Bucket "

        column_width = 20
        wrapped_column1 = textwrap.fill(column1, column_width)
        wrapped_column2 = textwrap.fill(column2, column_width)
        wrapped_column3 = textwrap.fill(column3, column_width)
        wrapped_column4 = textwrap.fill(column4, column_width)
        wrapped_column5 = textwrap.fill(column5, column_width)
        lines1 = wrapped_column1.split('\n')
        lines2 = wrapped_column2.split('\n')
        lines3 = wrapped_column3.split('\n')
        lines4 = wrapped_column4.split('\n')
        lines5 = wrapped_column5.split('\n')

        self.print_and_log("-" * 114)
        for line1, line2, line3, line4, line5 in zip(lines1, lines2, lines3, lines4, lines5):
                self.print_and_log(f"| {line1.center(column_width)} | {line2.center(column_width)} | {line3.center(column_width)} | {line4.center(column_width)} | {line5.center(column_width)} |")

        self.print_and_log("-" *114)

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
        if self.ec2_ro_access_flag == True:
            self.print_and_log("[EC2-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM")
        else:
            comments = "[EC2-log] AmazonEC2ReadOnlyAccess policy NOT attached with grading IAM."
            self.print_and_log(comments)
        try:
            web_instances = self.get_instance_details(self.web_tier_tag, 'running')
            app_instances = self.get_instance_details(self.app_tier_tag, 'running')
            self.print_and_log(f"[EC2-log] Found {web_instances} web-tier instances in running state.")
            self.print_and_log(f"[EC2-log] Found {app_instances} app-tier instances in running state")
            message = f"Found {web_instances} web-tier instances in running state. Found {app_instances} app-tier instances in running state"

            if not web_instances:
                points_deducted = 100
                comment = f"[EC2-log] Web tier state validation failed. {message}.Points deducted: {points_deducted}"
                self.print_and_log_error(comment)
                return points_deducted, comment

            if app_instances > 0:
                points_deducted = 70
                comment = f"[EC2-log] App tier state validation failed. {message}.Points deducted: {points_deducted}"
                self.print_and_log_error(comment)
                return points_deducted, comment

            if web_instances == 1 and app_instances == 0:
                points_deducted = 0
                comment = f"[EC2-log] EC2-state validation Pass. {message}.Points deducted: {points_deducted}"
                self.print_and_log(comment)
                return points_deducted, comment

        except (ClientError, Exception) as e:
            points_deducted = 100
            comments = f"[EC2-log] EC2-state validation failed {e}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def empty_s3_bucket(self, bucket_name):
        bucket = self.s3_resources.Bucket(bucket_name)
        bucket.objects.all().delete()
        self.print_and_log(f"[S3-log] Bucket:{bucket_name} is now EMPTY !!")

    def get_sqs_queue_length(self, sqs_queue_name):
        num_requests = self.sqs_client.get_queue_attributes(QueueUrl=sqs_queue_name, AttributeNames=['ApproximateNumberOfMessages'])
        return int(num_requests['Attributes']['ApproximateNumberOfMessages'])

    def count_bucket_objects(self, bucket_name):
        bucket = self.s3_resources.Bucket(bucket_name)
        count  = 0
        for index in bucket.objects.all():
            count += 1
        return count

    def validate_sqs_queues(self):
        points_deducted             = 0
        q_msg_size_pts_deduction    = 20
        q_msg_count_pts_deduction   = 5

        self.print_and_log("[SQS-log] The expectation is that both the Request and Response SQS should exist with max message size set to 1KB and be EMPTY")
        self.print_and_log("[SQS-log] - WARN: This will purge any messages available in the SQS")
        self.print_and_log("[SQS-log] ---------------------------------------------------------")

        if self.sqs_full_access_flag == True:
            self.print_and_log("[SQS-log] AmazonSQSFullAccess policy attached with grading IAM")
        else:
            comments = "[SQS-log] AmazonSQSFullAccess policy NOT attached with grading IAM"
            self.print_and_log(comments)

        try:
            req_sqs  = self.sqs_resources.get_queue_by_name(QueueName=self.req_sqs_name)
            resp_sqs = self.sqs_resources.get_queue_by_name(QueueName=self.resp_sqs_name)

            ip_queue_requests = int(self.sqs_client.get_queue_attributes(QueueUrl=self.req_sqs_name, AttributeNames=['ApproximateNumberOfMessages'])['Attributes']['ApproximateNumberOfMessages'])
            op_queue_response = int(self.sqs_client.get_queue_attributes(QueueUrl=self.resp_sqs_name, AttributeNames=['ApproximateNumberOfMessages'])['Attributes']['ApproximateNumberOfMessages'])

            ip_queue_msg_size = int(self.sqs_client.get_queue_attributes(QueueUrl=self.req_sqs_name,  AttributeNames=['MaximumMessageSize'])['Attributes']['MaximumMessageSize'])
            op_queue_msg_size = int(self.sqs_client.get_queue_attributes(QueueUrl=self.resp_sqs_name, AttributeNames=['MaximumMessageSize'])['Attributes']['MaximumMessageSize'])

            comments = f"[SQS-log] SQS Request Queue:{self.req_sqs_name} has {ip_queue_requests} pending messages with max message size set to {ip_queue_msg_size // 1024} KB.\n"
            comments += f"[SQS-log] SQS Response Queue:{self.resp_sqs_name} has {op_queue_response} pending messages.\n"

            if ip_queue_msg_size != 1024:
                points_deducted += q_msg_size_pts_deduction

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
            points_deducted += q_msg_size_pts_deduction + q_msg_count_pts_deduction
            comments = f"[SQS-log] SQS validation failed {ex}.Points deducted:{points_deducted}"
            self.print_and_log_error(comments)
            return points_deducted, comments

    def validate_s3_buckets(self):
        points_deducted             = 0
        s3_bkt_count_pts_deduction  = 5

        if self.s3_full_access_flag == True:
            self.print_and_log("[S3-log] AmazonS3FullAccess policy attached with grading IAM")
        else:
            comments = "[S3-log] AmazonS3FullAccess policy NOT attached with grading IAM"
            self.print_and_log(comments)

        try:
            self.print_and_log("[S3-log] - WARN: If there are objects in the S3 buckets; they will be deleted")
            self.print_and_log("[S3-log] ---------------------------------------------------------")

            in_bucket       = self.s3_resources.Bucket(self.in_bucket_name)
            ip_obj_count    = sum(1 for _ in in_bucket.objects.all())

            out_bucket      = self.s3_resources.Bucket(self.out_bucket_name)
            op_obj_count    = sum(1 for _ in out_bucket.objects.all())

            comments = f"[S3-log] S3 Bucket:{self.in_bucket_name} has {ip_obj_count} object(s).\n"
            comments += f"[S3-log] S3 Bucket:{self.out_bucket_name} has {op_obj_count} object(s).\n"

            if ip_obj_count or op_obj_count:
                points_deducted = s3_bkt_count_pts_deduction
                if ip_obj_count:
                    self.empty_s3_bucket(self.in_bucket_name)
                if op_obj_count:
                    self.empty_s3_bucket(self.out_bucket_name)
            else:
                points_deducted = 0

            comments += f"[S3-log] Points deducted:{points_deducted}"
            self.print_and_log(comments)
            return points_deducted, comments

        except (ClientError, Exception) as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                points_deducted = s3_bkt_count_pts_deduction
                comments = f"[S3-log] Bucket:{self.in_bucket_name} does not exist.Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                return points_deducted, comments
            else:
                points_deducted = s3_bkt_count_pts_deduction
                comments = f"[S3-log] Bucket:{self.in_bucket_name} validation failed due to: {e}.Points deducted:{points_deducted}"
                self.print_and_log_error(comments)
                return points_deducted, comments


    def parse_workload_stats(self, stdout):
        stats = {}
        stats["total_requests"]      = int(re.search(r"Total number of requests: (\d+)", stdout).group(1))
        stats["completed_requests"]  = int(re.search(r"Total number of requests completed successfully: (\d+)", stdout).group(1))
        stats["failed_requests"]     = int(re.search(r"Total number of failed requests: (\d+)", stdout).group(1))
        stats["correct_predictions"] = int(re.search(r"Total number of correct predictions : (\d+)", stdout).group(1))
        stats["wrong_predictions"]   = int(re.search(r"Total number of wrong predictions: (\d+)", stdout).group(1))
        stats["total_resp_time"]     = float(re.search(r"Total response time:\s*([0-9]+\.[0-9]+)", stdout).group(1))
        return stats

    def empty_s3_bucket(self, bucket_name):
        bucket = self.s3_resources.Bucket(bucket_name)
        bucket.objects.all().delete()
        self.print_and_log(f"[S3-log] Bucket:{bucket_name} is now EMPTY !!")

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
        time.sleep(10)
        stats = self.parse_workload_stats(stdout_output)
        return stats

    def validate_s3_bucket(self, bucket_name, num_req):
        total_s3_count_score   = 5
        s3_bucket_count     = self.count_bucket_objects(bucket_name)
        points_per_s3_entry = total_s3_count_score / num_req
        test_case_points    = s3_bucket_count* points_per_s3_entry
        test_case_points    = min(test_case_points, total_s3_count_score)
        test_case_points    = round(test_case_points, 2)
        comments = f"[Test-Case-3-log] {s3_bucket_count}/{num_req} entries in S3 bucket:{bucket_name}.Points:[{test_case_points}/{total_s3_count_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def validate_completeness(self, num_req, stats):
        total_completion_score = 10
        points_per_request = total_completion_score / num_req
        completed_requests = stats.get("completed_requests", 0)
        test_case_points   = completed_requests * points_per_request
        test_case_points   = min(test_case_points, total_completion_score)
        test_case_points   = round(test_case_points, 2)
        comments = f"[Test-Case-3-log] {completed_requests}/{num_req} completed successfully.Points:[{test_case_points}/{total_completion_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def validate_correctness(self, num_req, stats):
        total_correctness_score = 10
        points_per_request = total_correctness_score / num_req
        correct_prediction = stats.get("correct_predictions", 0)
        test_case_points   = correct_prediction * points_per_request
        test_case_points   = min(test_case_points, total_correctness_score)
        test_case_points   = round(test_case_points, 2)
        comments = f"[Test-Case-3-log] {correct_prediction}/{num_req} correct predictions.Points:[{test_case_points}/{total_correctness_score}]"
        self.print_and_log(comments)
        return test_case_points, comments

    def validate_scale_in_latency(self):
        scale_in_lat_points  = 10
        points_deducted      = 0
        timeout              = 5
        comments             = ""

        start_time = time.time()
        while time.time() - start_time < timeout:
            num_instances = self.get_instance_details(self.app_tier_tag, 'running')
            if num_instances == 0:
                break
        end_time = time.time()
        total_time = end_time - start_time

        if num_instances == 0:
            if total_time < 2:
                points_deducted = 0
                score = 10
            elif 2 <= total_time <= 5:
                points_deducted = 5
            else:
                points_deducted = scale_in_lat_points
        else:
            points_deducted = scale_in_lat_points
            comments = f"[AS-log] App tier instances did not scale in to 0 within 5 seconds after workload completion. Remaining running instances: {num_instances}\n"

        comments += f"[AS-log] Time to scale in to {num_instances} instances: {total_time:.2f} seconds.Points:[{scale_in_lat_points - points_deducted}/{scale_in_lat_points}]"
        self.print_and_log(comments)
        return (scale_in_lat_points - points_deducted), comments

    def validate_latency(self, num_req, stats):
        total_test_score = 40
        completed_requests  = stats.get("completed_requests", 0)
        latency             = stats.get("total_resp_time", 0)
        comments            = ""

        if completed_requests == num_req:
            avg_latency         = latency / completed_requests
            if avg_latency > 0:
                deductions = [(1.2, 0, "avg latency<1.2s"),
                        (2.1, 20, "avg latency>=1.2s and avg latency<2.1s"),
                        (3, 30, "avg latency>=2.1s and avg latency<3"),
                        (float('inf'), 40, "avg latency>4.2")]

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

    def validate_autoscaling(self, stop_event, as_resultq):

        try:
            self.print_and_log("[AS-log] - Autoscaling validation starts ..")
            self.print_and_log("[AS-log] - The expectation is as follows:")
            self.print_and_log("[AS-log]  -- # of app tier instances should gradually scale and eventually reduce back to 0")
            self.print_and_log("[AS-log]  -- # of SQS messages should gradually increase and eventually reduce back to 0")
            self.beautify_headers()
            format_string = "| {:^20} | {:^20} | {:^20} | {:^20} | {:^20} |"

            autoscaling_data = []

            while not stop_event.is_set():
                req_queue_count  = self.get_sqs_queue_length(self.req_sqs_name)
                resp_queue_count = self.get_sqs_queue_length(self.resp_sqs_name)
                num_instances    = self.get_instance_details(self.app_tier_tag, 'running')
                ip_obj_count     = self.count_bucket_objects(self.in_bucket_name)
                op_obj_count     = self.count_bucket_objects(self.out_bucket_name)
                data_point = (req_queue_count, resp_queue_count, num_instances, ip_obj_count, op_obj_count)
                autoscaling_data.append(data_point)
                self.print_and_log(format_string.format(req_queue_count, resp_queue_count, num_instances, ip_obj_count, op_obj_count))
                self.print_and_log("-" * 114)
                time.sleep(2)

            as_resultq.put(autoscaling_data)
        except Exception as e:
            self.print_and_log_error(f"[AS-log] Error in validate_autoscaling: {e}")
            as_resultq.put([])

    def check_ec2_pattern(self, num_instances):

        status           = True
        scale_out_points = 15
        scale_in_points  = 5
        points_deducted  = 0
        comments         = ""

        if num_instances[0] != 0:
            points_deducted += scale_out_points
            points_deducted += scale_in_points

            comments += f"[AS-log] Instances did not start from 0.Points deducted:{points_deducted}\n"
            self.print_and_log_error(f"[AS-log] Instances did not start from 0.Points deducted:{points_deducted}")
            status = False
            return (scale_out_points + scale_in_points - points_deducted), comments

        ec2_scale_out       = any(x > 0 for x in num_instances) and max(num_instances) == self.max_ec2_instances
        ec2_scale_in        = ec2_scale_out and num_instances[-1] == 0
        max_instance_status = True

        for i in range(1, len(num_instances)):
            if num_instances[i] > self.max_ec2_instances:
                comments += f"[AS-log] EC2 Instances exceeded the limit of {self.max_ec2_instances} at step {i} (count: {num_instances[i]}).\n"
                self.print_and_log_error(f"[AS-log] EC2 Instances exceeded the limit of {self.max_ec2_instances} at step {i} (count: {num_instances[i]})")
                status = False
                max_instance_status = False

        if max_instance_status == False or not ec2_scale_out:
            if max_instance_status == False:
                self.print_and_log_error(f"[AS-log] EC2 Instances exceeded the limit of {self.max_ec2_instances}. EC2 instances did not scale out as expected.")

            comments += f"[AS-log] EC2 instances did not scale out as expected.\n"
            comments += f"[AS-log] Points deducted:{scale_out_points}"
            self.print_and_log_error(f"[AS-log] EC2 instances did not scale out as expected. Points deducted: {scale_out_points}")
            status = False
            points_deducted += scale_out_points
        else:
            comments += f"[AS-log] EC2 instances scale out as expected. Points:[{scale_out_points}/{scale_out_points}]\n"
            self.print_and_log_error(f"[AS-log] EC2 instances scale out as expected. Points:[{scale_out_points}/{scale_out_points}]")

        if ec2_scale_in:
            comments += f"[AS-log] EC2 instances scale back to 0 as expected. Points:[{scale_in_points}/{scale_in_points}]\n"
            self.print_and_log_error(f"[AS-log] EC2 instances scale back to 0 as expected. Points:[{scale_in_points}/{scale_in_points}]")
        else:
            comments += f"[AS-log] EC2 instances did not scale back to 0 as expected. Points deducted: {scale_in_points}\n"
            self.print_and_log_error(f"[AS-log] EC2 instances did not scale back to 0 as expected. Points deducted: {scale_in_points}")
            status = False
            points_deducted += scale_in_points

        return (scale_out_points + scale_in_points - points_deducted), comments


    def check_s3_pattern(self, bucket_name, bucket_counts):
        status = True
        if bucket_counts[0] != 0:
            self.print_and_log_error(f"[AS-log] S3 bucket:{bucket_name} counts do not start at 0.")
            status = False

        increasing      = False
        peak_reached    = False

        for i in range(1, len(bucket_counts)):
            if bucket_counts[i] > bucket_counts[i - 1]:
                increasing = True

        if increasing and max(bucket_counts) == self.num_req:
            self.print_and_log(f"[AS-log] S3 bucket:{bucket_name} objects increased from 0 to {self.num_req}.")
            status = True
        else:
            self.print_and_log_error(f"[AS-log] S3 bucket:{bucket_name} pattern is not as expected.")
            status = False

        self.empty_s3_bucket(bucket_name)


    def check_sqs_pattern(self, sqs_queue_name, req_queue_counts):

        status          = True
        sqs_as_points   = 5
        points_deducted = 0
        comments        = ""

        if req_queue_counts[0] != 0 or req_queue_counts[-1] != 0:
            points_deducted += sqs_as_points
            comments += f"[AS-log] SQS messages in {sqs_queue_name} do not start and end at 0. Points deducted: {points_deducted}\n"
            self.print_and_log_error(f"[AS-log] SQS messages in {sqs_queue_name} do not start and end at 0. Points deducted: {points_deducted}")
            return (sqs_as_points - points_deducted), comments

        if sqs_queue_name == self.req_sqs_name:
            increasing      = False
            peak_reached    = False

            for i in range(1, len(req_queue_counts)):
                if req_queue_counts[i] > req_queue_counts[i - 1]:
                    increasing = True
                elif req_queue_counts[i] < req_queue_counts[i - 1] and increasing:
                    peak_reached = True

            if increasing and peak_reached:
                comments += f"[AS-log] SQS messages in {sqs_queue_name} increased from 0 and reduced back to 0. Points:[{sqs_as_points}/{sqs_as_points}]\n"
                self.print_and_log(f"[AS-log] SQS messages in {sqs_queue_name} increased from 0 and reduced back to 0. Points:[{sqs_as_points}/{sqs_as_points}]")
            else:
                points_deducted += sqs_as_points
                comments += f"[AS-log] SQS message pattern in {sqs_queue_name} is not as expected. Points deducted: {points_deducted}\n"
                self.print_and_log_error(f"[AS-log] SQS message pattern in {sqs_queue_name} is not as expected. Points deducted: {points_deducted}")
        else:
            comments += f"[AS-log] SQS messages in {sqs_queue_name} increased from 0 and reduced back to 0. Points:[{sqs_as_points}/{sqs_as_points}]\n"
            self.print_and_log(f"[AS-log] SQS messages in {sqs_queue_name} increased from 0 and reduced back to 0. Points:[{sqs_as_points}/{sqs_as_points}]")

        return (sqs_as_points - points_deducted), comments


    def analyze_autoscaling_results(self, autoscaling_data):

        sqs_as_points = 0
        ec2_as_points = 0
        autoscaling_status = True

        if not autoscaling_data:
            comments = f"[AS-log] No data available to analyze autoscaling results."
            self.print_and_log_error(comments)
            return False, 0, comments, 0, comments

        req_queue_counts 	= [data[0] for data in autoscaling_data]
        resp_queue_counts 	= [data[1] for data in autoscaling_data]
        num_instances 		= [data[2] for data in autoscaling_data]
        ip_bucket_counts    = [data[3] for data in autoscaling_data]
        op_bucket_counts    = [data[4] for data in autoscaling_data]

        # Check instances pattern
        ec2_as_points, ec2_as_comments = self.check_ec2_pattern(num_instances)

        # Check SQS queues pattern
        req_sqs_as_points, req_sqs_as_comments   = self.check_sqs_pattern(self.req_sqs_name, req_queue_counts)
        resp_sqs_as_points, resp_sqs_as_comments = self.check_sqs_pattern(self.resp_sqs_name, resp_queue_counts)
        sqs_as_points    = req_sqs_as_points + resp_sqs_as_points
        sqs_as_comments  = req_sqs_as_comments
        sqs_as_comments += resp_sqs_as_comments

        # Check S3 buckets pattern
        self.check_s3_pattern(self.in_bucket_name, ip_bucket_counts)
        self.check_s3_pattern(self.out_bucket_name, op_bucket_counts)

        return autoscaling_status, ec2_as_points, ec2_as_comments, sqs_as_points, sqs_as_comments

    def evaluate_iaas(self, num_req, ip_addr, img_folder, pred_file):

        self.num_req = num_req
        stop_event   = threading.Event()
        as_resultq   = queue.Queue()

        # Create a thread for validate_autoscaling
        validate_autoscaling_thread = threading.Thread(target=self.validate_autoscaling, args=(stop_event, as_resultq))
        test_case_points = 0
        stats            = {}

        try:
            # Start the validate_autoscaling thread
            validate_autoscaling_thread.start()

            stats = self.run_workload_generator(num_req, ip_addr, img_folder, pred_file)

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            comments = ""
            self.print_and_log_error(f"[Test-Case-log] Workload generator failed with return code {e}")
            self.print_and_log_error(f"[Test-Case-log] Standard output: {e.stdout}")
            self.print_and_log_error(f"[Test-Case-log] Standard error: {e.stderr}")
            comments = f"[Test-Case-log] Error: {e.stdout} + {e.stderr}"
            return 0, comments
        finally:

            self.print_and_log("[Test-Case-3-log] Waiting for 5sec for the resources to scale in ...")
            scale_in_lat_score, scale_in_lat_log = self.validate_scale_in_latency()
            stop_event.set()
            self.print_and_log("[Test-Case-3-log] Stop event set. Waiting for autoscaling thread to finish.")
            validate_autoscaling_thread.join()

            in_s3_score,  in_s3_log              = self.validate_s3_bucket(self.in_bucket_name, num_req)
            out_s3_score, out_s3_log             = self.validate_s3_bucket(self.out_bucket_name, num_req)
            #completeness_score, completeness_log = self.validate_completeness(num_req, stats)
            correctness_score, correctness_log   = self.validate_correctness(num_req, stats)
            latency_score, latency_log           = self.validate_latency(num_req, stats)
            self.print_and_log("[Test-Case-3-log] ---------------------------------------------------------")

            test_case_points += scale_in_lat_score + in_s3_score + out_s3_score + correctness_score + latency_score
            comments = scale_in_lat_log
            comments += in_s3_log
            comments += out_s3_log
            comments += correctness_log
            comments += latency_log

			# Retrieve the result from the validate_autoscaling thread
            if not as_resultq.empty():
                autoscaling_result = as_resultq.get()
                #self.print_and_log(f"Autoscaling Data: {autoscaling_result}")
                status, ec2_as_points, ec2_as_comments, sqs_as_points, sqs_as_comments = self.analyze_autoscaling_results(autoscaling_result)
                self.print_and_log("[AS-log] ---------------------------------------------------------")

                test_case_points += ec2_as_points + sqs_as_points
                comments += ec2_as_comments
                comments += sqs_as_comments
            else:
                autoscaling_result = None
                self.print_and_log_error("No data collected from autoscaling.")

            return test_case_points, comments


    def validate_initial_states(self):
        ec2_pts_deducted, ec2_logs = self.validate_ec2_state()
        s3_pts_deducted, s3_logs   = self.validate_s3_buckets()
        sqs_pts_deducted, sqs_logs = self.validate_sqs_queues()

        total_points_deducted = ec2_pts_deducted + s3_pts_deducted + sqs_pts_deducted
        comments = ec2_logs
        comments += s3_logs
        comments += sqs_logs

        return (-1*total_points_deducted), comments

    def main(self, num_req, ip_addr, img_folder, pred_file):
        test_results = {}

        self.print_and_log("-------------- CSE546 Cloud Computing Grading Console -----------")
        self.print_and_log(f"IAM ACCESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(f"IAM SECRET ACCESS KEY: {self.iam_secret_access_key}")
        self.print_and_log(f"Web-Instance IP Address: {ip_addr}")
        self.print_and_log("-----------------------------------------------------------------")

        self.print_and_log("----------------- Executing Test-Case:1 ----------------")
        test_results["tc_2"] = self.validate_initial_states()
        self.print_and_log("----------------- Executing Test-Case:2 ----------------")
        test_results["tc_3"] = self.evaluate_iaas(num_req, ip_addr, img_folder, pred_file)

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
