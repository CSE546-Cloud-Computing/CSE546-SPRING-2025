
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
import argparse
from botocore.exceptions import ClientError

class iam_policies():
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

        self.print_and_log(self.logger, "-----------------------------------------------------------------")
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
            self.print_and_log(self.logger, "[IAM-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM")
        else:
            policy_exits = False
            self.print_and_log_error(self.logger, "[IAM-log] AmazonEC2ReadOnlyAccess policy NOT attached with grading IAM")
        return policy_exits

        '''
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

                self.print_and_log_error(self.logger, f"[IAM-log] Waiting for the instance project0  to change state to running")
                instance = new_instance[0]
                instance.wait_until_running()
                instance.load()
                self.print_and_log_error(self.logger, f"[IAM-log] A new EC2 instance:project0 was created with InstanceId:{ instance.id}")
                return False

            except ClientError as e:
                if e.response['Error']['Code'] == 'UnauthorizedOperation':
                    comments = "[IAM-log] EC2 instance creation failed with UnauthorizedOperation error. This is as expected."
                    self.print_and_log(self.logger, comments)
                    return True
        else:
            comments = "[IAM-log] AmazonEC2ReadOnlyAccess policy NOT attached with grading IAM."
            self.print_and_log_error(self.logger, comments)
            return False
        '''


    def validate_sqs_queues(self, attached_policies):

        if "AmazonSQSReadOnlyAccess" in attached_policies:
            policy_exits = True
            self.print_and_log(self.logger, "[IAM-log] AmazonSQSReadOnlyAccess policy attached with grading IAM")
        else:
            policy_exits = False

        if policy_exits:
            try:
                self.print_and_log(self.logger, "[IAM-log] Trying to create a SQS queue")
                response = self.requestQ.create_queue(QueueName = "test-sqs")
                comments = "[IAM-log] SQS queue successfully created. This is NOT expected."
                self.print_and_log_error(self.logger, comments)
                return False
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDenied':
                    comments = "[IAM-log] SQS creation failed with Access Denied error. This is expected."
                    self.print_and_log(self.logger, comments)
                    return True
        else:
            comments = "[IAM-log] AmazonSQSReadOnlyAccess policy NOT attached with grading IAM."
            self.print_and_log_error(self.logger, comments)
            return False

    def validate_s3(self, attached_policies):

        if "AmazonS3FullAccess" in attached_policies:
            policy_exits = True
            self.print_and_log(self.logger, "[IAM-log] AmazonS3FullAccess policy attached with grading IAM")
        else:
            policy_exits = False
            comments = "[IAM-log] AmazonS3FullAccess policy NOT attached with grading IAM."
            self.print_and_log_error(self.logger, comments)

        return policy_exits

    def validate_policies(self):

        try:
            attached_policies = self.iam_client.list_attached_user_policies(UserName='cse546-AutoGrader',
                                                                            MaxItems=100)
            policy_names = [policy['PolicyName'] for policy in attached_policies['AttachedPolicies']]
            self.print_and_log(self.logger, f"Following policies are attached with IAM user:cse546-AutoGrader: {policy_names}")

            iam_ro_access_flag  = True
            ec2_ro_access_flag  = self.validate_ec2_instance(policy_names)
            s3_full_access_flag = self.validate_s3(policy_names)
            return iam_ro_access_flag, ec2_ro_access_flag, s3_full_access_flag

        except ClientError as e:
            iam_ro_access_flag   = False
            ec2_ro_access_flag   = None
            s3_full_access_flag  = None
            self.print_and_log_error(self.logger, f"Failed to fetch the attached polices. {e}")
            return iam_ro_access_flag, ec2_ro_access_flag, s3_full_access_flag

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload images')
    parser.add_argument('--access_keyId', type=str, help='ACCCESS KEY ID of the grading IAM user')
    parser.add_argument('--access_key', type=str, help='SECRET ACCCESS KEY of the grading IAM user')
    log_file = 'autograder.log'
    logging.basicConfig(filename=log_file, level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args         = parser.parse_args()
    access_keyId = args.access_keyId
    access_key   = args.access_key
    iam_obj      = iam_policies(logger, access_keyId, access_key)
    iam_obj.validate_policies()

