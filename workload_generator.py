__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

import os
import sys
import pdb
import json
import uuid
import time
import boto3
import base64
import _thread
import argparse
import requests
import subprocess
import numpy as np
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

parser = argparse.ArgumentParser(description='workload generator')
parser.add_argument('--num_request', type=int, help='one image per request')
parser.add_argument('--lambda_url', type=str, help='url of the entry lambda fucntion')
parser.add_argument('--response_queue_url', type=str, help='url of the Response SQS Queue')
parser.add_argument('--image_folder', type=str, help='the path of the folder where images are saved')
parser.add_argument('--prediction_file', type=str, help='the path of the classification results file')
args = parser.parse_args()

num_request         = args.num_request
lambda_url          = args.lambda_url
response_queue_url  = args.response_queue_url
image_folder        = args.image_folder
prediction_file     = args.prediction_file
passed_requests     = 0
failed_requests     = 0
correct_predictions = 0
wrong_predictions   = 0
prediction_df       = pd.read_csv(prediction_file)


sqs = boto3.client("sqs")

def poll_response(sqs, request_id, response_queue_url):
    """ Poll SQS response queue for the result """

    max_wait_time 	= 300
    poll_start 		= time.time()

    #print(f"Polling for response from Face recognition...")

    while time.time() - poll_start < max_wait_time:
        try:
            response_messages = sqs.receive_message(
                    QueueUrl=response_queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=5,
                    MessageAttributeNames=["All"]
                    )

            if "Messages" in response_messages:
                for message in response_messages["Messages"]:
                    response_body = json.loads(message["Body"])
                    #print(f"Received response: {response_body}")

                    message_request_id  = response_body.get("request_id", "")
                    message_label       = response_body.get("result", "")
                    if message_request_id == request_id:
                        #print(f"Received response: {response_body}")
                        try:
                            sqs.delete_message(
                                    QueueUrl=response_queue_url,
                                    ReceiptHandle=message["ReceiptHandle"]
                                    )
                            #print(f"Successfully deleted message with request id:{request_id} from SQS response queue")
                        except Exception as delete_error:
                            print(f"Error deleting message from SQS: {delete_error}")

                        #return response_body
                        return message_label

            print(f"Polling SQS Response queue for request id:{request_id}")

        except Exception as e:
            print(f"Error polling SQS: {e}")
            return None

    # If no response received within max_wait_time
    return {"error": "Timeout waiting for response from Face recognition"}


def send_one_request(image_path):
    global lambda_url, prediction_df, passed_requests, failed_requests, correct_predictions, wrong_predictions, sqs, response_queue_url

    try:
        with open(image_path, "rb") as f:
            encoded_file = base64.b64encode(f.read()).decode("utf-8")  # Convert bytes to string
        request_id 	= str(uuid.uuid4())
        payload 	= json.dumps({"request_id": request_id, "content": encoded_file, "filename": image_path})

        # Headers (set Content-Type to JSON)
        headers = {"Content-Type": "application/json"}

        # Send POST request
        response = requests.post(lambda_url, data=payload, headers=headers)
        print(f"Response from Face Detection: {response.text}")

        # Print error message if failed
        if response.status_code != 200:
            print('sendErr: '+response.url)
            #print(response)
            failed_requests +=1
        else :
            filename    = os.path.basename(image_path)
            image_msg   = filename + f' uploaded to face-detection lambda with request_id:{request_id}!'
            msg         = image_msg + ' === '
            #msg         = image_msg + ' === ' + response.text
            #print(f"[Workload-gen] {msg}")
            passed_requests   +=1

            # start polling the Response Queue for face recognition labels
            recognition_label = poll_response(sqs, request_id, response_queue_url)
            #print(f"Results from Face Recognition: {recognition_label}")

            ground_truth     = prediction_df.loc[prediction_df['Image'] == filename, 'Results'].values[0]

            #response_data = json.loads(response.text)
            #print(response_data)

            #print(f"Ground Truth:{ground_truth} PL:{recognition_label}")

            if ground_truth.strip() == recognition_label:
                correct_predictions +=1
            else:
                wrong_predictions +=1

    except (requests.exceptions.RequestException, Exception) as errex:
        print("Exception:", errex)
        failed_requests +=1

num_max_workers = 100
image_path_list = []

for i, name in enumerate(os.listdir(image_folder)):
    if i == num_request:
        break
    image_path_list.append(os.path.join(image_folder,name))

test_start_time = time.time()
batch_size      = 10
num_of_batches  = num_request // batch_size
delay_seconds   = 1

# Process requests in batches
for i in range(0, len(image_path_list), batch_size):
    batch                   = image_path_list[i : i + batch_size]
    batch_number            = i // batch_size + 1
    num_requests_in_batch   = len(batch)

    print(f"[Workload-gen] Processing batch {batch_number} with {num_requests_in_batch} requests...")

    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        executor.map(send_one_request, batch)

    time.sleep(delay_seconds)

test_duration   = time.time() - test_start_time
injected_delays = delay_seconds * num_of_batches
duration        = test_duration - injected_delays

print (f"[Workload-gen] ----- Workload Generator Statistics -----")
print (f"[Workload-gen] Total number of requests: {num_request}")
print (f"[Workload-gen] Total number of requests completed successfully: {passed_requests}")
print (f"[Workload-gen] Total number of failed requests: {failed_requests}")
print (f"[Workload-gen] Total number of correct predictions : {correct_predictions}")
print (f"[Workload-gen] Total number of wrong predictions: {wrong_predictions}")
print (f"[Workload-gen] Total duration: {test_duration} (seconds)")
print (f"[Workload-gen] Test Latency: {duration} (seconds)")
print (f"[Workload-gen] -----------------------------------")
