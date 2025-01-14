
__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

"""
File: grade_project0.py
Author: Kritshekhar Jha
Date: 2025-01-01
Description: Grading script for Project-0
"""

import os
import pdb
import json
import httpx
import boto3
import dotenv
import logging
import argparse
from botocore.exceptions import ClientError

class aws_grader():
    def __init__(self, logger, access_keyId, access_key):

        self.iam_access_keyId       = access_keyId
        self.iam_secret_access_key  = access_key
        self.iam_session            = boto3.Session(aws_access_key_id = self.iam_access_keyId,
                                                    aws_secret_access_key = self.iam_secret_access_key)
        self.ec2_resources          = self.iam_session.resource('ec2', 'us-east-1')
        self.s3_resources           = self.iam_session.resource('s3', 'us-east-1')
        self.iam_client             = self.iam_session.client("iam", 'us-east-1')
        self.iam_resource           = self.iam_session.resource("iam", 'us-east-1')
        self.requestQ               = self.iam_session.client('sqs', 'us-east-1')
        self.logger                 = logger

        self.print_and_log(self.logger, "-------------- CSE546 Cloud Computing Grading Console -----------")
        self.print_and_log(self.logger, f"IAM ACESS KEY ID: {self.iam_access_keyId}")
        self.print_and_log(self.logger, f"IAM SECRET ACCESS KEY: {self.iam_secret_access_key}")
        self.print_and_log(self.logger, "-----------------------------------------------------------------")

    def print_and_log(self, logger, message):
        print(message)
        logger.info(message)

    def print_and_log_error(self, logger, message):
        print(message)
        logger.error(message)

    def get_tag(self, tags, key='Name'):

        if not tags:
            return 'None'
        for tag in tags:
            if tag['Key'] == key:
                return tag['Value']
        return 'None'

    def validate_ec2_instance(self, attached_policies):

        if "AmazonEC2ReadOnlyAccess" in attached_policies:
            policy_exits = True
            self.print_and_log(self.logger, "[EC2-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM")
        else:
            policy_exits = False

        if policy_exits:
            try:
                self.print_and_log(self.logger, "[EC2-log] Trying to create a EC2 instance")

                TAG_SPEC = [{"ResourceType":"instance","Tags": [{"Key": "Name","Value": "project0"}]}]
                new_instance  = self.ec2_resources.create_instances(
                        ImageId   = "ami-0a8b4cd432b1c3063",
                        MinCount  = 1,
                        MaxCount  = 1,
                        InstanceType ='t2.micro',
                        TagSpecifications = TAG_SPEC)

                self.print_and_log_error(self.logger, f"[EC2-log] Waiting for the instance project0  to change state to running")
                instance = new_instance[0]
                instance.wait_until_running()
                instance.load()

                self.print_and_log_error(self.logger, f"[EC2-log] A new EC2 instance:project0 was created with InstanceId:{ instance.id}")

                comments = "[EC2-log] EC2 instance was successfully created. This is NOT expected. Points:[0/33.33]"
                self.print_and_log_error(self.logger, comments)
                return 0, comments

            except ClientError as e:
                if e.response['Error']['Code'] == 'UnauthorizedOperation':
                    comments = "[EC2-log] EC2 instance creation failed with UnauthorizedOperation error. This is as expected. Points:[33.33/33.33]"
                    self.print_and_log(self.logger, comments)
                    return 33.33, comments
        else:
            comments = "[EC2-log] AmazonEC2ReadOnlyAccess policy NOT attached with grading IAM. Points:[0/33.33]"
            self.print_and_log_error(self.logger, comments)
            return 0, comments


    def validate_sqs_queues(self, attached_policies):

        if "AmazonSQSReadOnlyAccess" in attached_policies:
            policy_exits = True
            self.print_and_log(self.logger, "[SQS-log] AmazonSQSReadOnlyAccess policy attached with grading IAM")
        else:
            policy_exits = False

        if policy_exits:
            try:
                self.print_and_log(self.logger, "[SQS-log] Trying to create a SQS queue")
                response = self.requestQ.create_queue(QueueName = "test-sqs")
                comments = "[SQS-log] SQS queue successfully created. This is NOT expected. Points:[0/33.33]"
                self.print_and_log_error(self.logger, comments)

                return 0, comments
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDenied':
                    comments = "[SQS-log] SQS creation failed with Access Denied error. This is expected. Points:[33.33/33.33]"
                    self.print_and_log(self.logger, comments)
                    return 33.33,comments
        else:
            comments = "[SQS-log] AmazonSQSReadOnlyAccess policy NOT attached with grading IAM. Points:[0/33.33]"
            self.print_and_log_error(self.logger, comments)
            return 0, comments

    def validate_s3(self, attached_policies):

        if "AmazonS3ReadOnlyAccess" in attached_policies:
            policy_exits = True
            self.print_and_log(self.logger, "[S3-log] AmazonS3ReadOnlyAccess policy attached with grading IAM")
        else:
            policy_exits = False

        if policy_exits:
            try:
                self.print_and_log(self.logger, "[S3-log] Trying to create a S3 bucket")
                self.s3_resources.create_bucket(Bucket="test-bucket")
                comments = "[S3-log] Bucket successfully created. This is NOT expected. Points:[0/33.33]"
                self.print_and_log_error(self.logger, comments)

                return 0, comments
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDenied':
                    comments = "[S3-log] Bucket creation failed with Access Denied error. This is expected. Points:[33.33/33.33]"
                    self.print_and_log(self.logger, comments)
                    return 33.33, comments
        else:
            comments = "[S3-log] AmazonS3ReadOnlyAccess policy NOT attached with grading IAM. Points:[0/33.33]"
            self.print_and_log_error(self.logger, comments)
            return 0, comments

    def main(self, policy_names):

        self.print_and_log(self.logger, "----- Executing Test-Case:1 -----")
        tc_1_pts, tc_1_comments = self.validate_ec2_instance(policy_names)
        self.print_and_log(self.logger, "----- Executing Test-Case:2 -----")
        tc_2_pts, tc_2_comments = self.validate_s3(policy_names)
        self.print_and_log(self.logger, "----- Executing Test-Case:3 -----")
        tc_3_pts, tc_3_comments = self.validate_sqs_queues(policy_names)

        grade_points = tc_1_pts + tc_2_pts + tc_3_pts
        if grade_points == 99.99: grade_points = 100
        self.print_and_log(self.logger, f"Total Grade Points: {grade_points}")

        return tc_1_pts, tc_1_comments, tc_2_pts, tc_2_comments, tc_3_pts, tc_3_comments



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload images')
    parser.add_argument('--access_keyId', type=str, help='ACCCESS KEY ID of the grading IAM user')
    parser.add_argument('--access_key', type=str, help='SECRET ACCCESS KEY of the grading IAM user')
    log_file = 'autograder.log'
    logging.basicConfig(filename=log_file, level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args = parser.parse_args()
    access_keyId = args.access_keyId
    access_key   = args.access_key
    aws_obj = aws_grader(logger, access_keyId, access_key)

    attached_policies = aws_obj.iam_client.list_attached_user_policies(UserName='cse546-AutoGrader',
                                                                                    MaxItems=100)
    policy_names = [policy['PolicyName'] for policy in attached_policies['AttachedPolicies']]
    aws_obj.main(policy_names)

