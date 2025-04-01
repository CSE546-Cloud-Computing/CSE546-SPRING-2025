__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

"""
File: cloudWatch.py
Author: Kritshekhar Jha
Date: 2025-01-01
Description: Script to verify cloudwatch billing alarm
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

class aws_cloudwatch():
    def __init__(self, logger, access_keyId, access_key):

        self.iam_access_keyId       = access_keyId
        self.iam_secret_access_key  = access_key
        self.iam_session            = boto3.Session(aws_access_key_id = self.iam_access_keyId,
                                                    aws_secret_access_key = self.iam_secret_access_key)
        self.iam_client             = self.iam_session.client("iam", 'us-east-1')
        self.iam_resource           = self.iam_session.resource("iam", 'us-east-1')
        self.cloudwatch_client      = self.iam_session.client('cloudwatch', 'us-east-1')
        self.logger                 = logger

    def print_and_log(self, message):
        print(message)
        self.logger.info(message)

    def print_and_log_error(self, message):
        print(message)
        self.logger.error(message)

    def print_and_log_warn(self, message):
        print(message)
        self.logger.warning(message)

    def is_none_or_empty(self, string):
        return string is None or string.strip() == ""

    def validate_cloudwatch(self):
        alarm_found = ""
        try:
            alarms = self.cloudwatch_client.describe_alarms()
            metric_alarms = alarms['MetricAlarms']
            if len(metric_alarms):
                for alarm in metric_alarms:
                    name        = alarm['AlarmName']
                    alarm_arn   = alarm['AlarmArn']
                    state_value = alarm['StateValue']
                    statistic   = alarm['Statistic']
                    threshold   = alarm['Threshold']
                    operator    = alarm['ComparisonOperator']

                    self.print_and_log(f"[Cloudwatch-log] Alarm:{name} with ARN:{alarm_arn} found in state:{state_value}. It is configued with statistic:{statistic}, threshold:{threshold} and Comparison Operator:{operator}")

                    if (state_value == 'ALARM'):
                        self.print_and_log(f"[Cloudwatch-log] CAUTION !!! Billing alarm:{alarm_arn} is triggered. Release the unwanted resources")
                    if (state_value == 'OK'):
                        self.print_and_log(f"[Cloudwatch-log] Billing alarm:{alarm_arn} is not triggered.")
                    if (state_value == 'INSUFFICIENT_DATA'):
                        self.print_and_log(f"[Cloudwatch-log] The alarm:{alarm_arn} has just started, the metric is not available, or not enough data is available for the metric to determine the alarm state.")

                    if (statistic == 'Maximum' and operator == 'GreaterThanThreshold'):
                        alarm_found = "True"

                return alarm_found
            else:
                alarm_found = ""
                return alarm_found

        except ClientError as e:
            self.print_and_log_error(f"[Cloudwatch-log] AWS Cloudwatch validation failed: {e}")
            alarm_found = ""
            return alarm_found

    def main(self):
        alarm_found = self.validate_cloudwatch()
        if self.is_none_or_empty(alarm_found) == True:
            self.print_and_log_warn(f"[Cloudwatch-log] CAUTION !! You do not have a Cloudwatch alarm set. Kindly refer to the Project-0 document and learn how to set a billing alarm")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Cloudwatch billing alarm')
    parser.add_argument('--access_keyId', type=str, help='ACCCESS KEY ID of the grading IAM user')
    parser.add_argument('--access_key', type=str, help='SECRET ACCCESS KEY of the grading IAM user')

    log_file = 'autograder.log'
    logging.basicConfig(filename=log_file, level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    args = parser.parse_args()
    access_keyId = args.access_keyId
    access_key   = args.access_key
    aws_obj = aws_cloudwatch(logger, access_keyId, access_key)
    aws_obj.main()

