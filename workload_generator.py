import os
import json
import time
import uuid
import boto3
import base64
import argparse
import requests
import threading
import pandas as pd

# Argument parser
parser = argparse.ArgumentParser(description="Workload Generator")
parser.add_argument("--access_keyID", type=str, help="access key id of the iam user")
parser.add_argument("--access_key", type=str, help="access key of the iam user")
parser.add_argument("--num_request", type=int, help="Total number of requests to send")
parser.add_argument("--lambda_url", type=str, help="URL of the entry Lambda function")
parser.add_argument("--response_queue_url", type=str, help="URL of the Response SQS Queue")
parser.add_argument("--image_folder", type=str, help="Path of the folder where images are saved")
parser.add_argument("--prediction_file", type=str, help="Path of the classification results file")
args = parser.parse_args()

# Load arguments
access_keyid        = args.access_keyID
access_key          = args.access_key
num_request         = args.num_request
lambda_url          = args.lambda_url
response_queue_url  = args.response_queue_url
image_folder        = args.image_folder
prediction_file     = args.prediction_file
#timer_interval      = args.timer_interval

# AWS SQS client
iam_session         = boto3.Session(aws_access_key_id = access_keyid,
                                    aws_secret_access_key = access_key)
sqs                 = iam_session.client('sqs',    'us-east-1')

# Tracking statistics
passed_requests     = 0
failed_requests     = 0
correct_predictions = 0
wrong_predictions   = 0
image_index         = 0
prediction_df       = pd.read_csv(prediction_file)

# Load image paths
image_path_list = [
    os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith((".jpg", ".png"))
]

image_index     = 0
active_requests = 0
lock            = threading.Lock()

# Time interval (in seconds) between requests
timer_interval = 1
#print(f"Timer interval: {timer_interval}")

def poll_response(sqs, request_id, response_queue_url):
    """Poll the SQS response queue for the result."""
    max_wait_time = 300
    poll_start = time.time()

    while time.time() - poll_start < max_wait_time:
        try:
            response_messages = sqs.receive_message(
                QueueUrl=response_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5,
                MessageAttributeNames=["All"],
            )

            if "Messages" in response_messages:
                for message in response_messages["Messages"]:
                    response_body = json.loads(message["Body"])
                    received_request_id = response_body.get("request_id", "")

                    if received_request_id == request_id:
                        #print(f"Received response for {request_id}")

                        try:
                            sqs.delete_message(
                                QueueUrl=response_queue_url,
                                ReceiptHandle=message["ReceiptHandle"],
                            )
                        except Exception as delete_error:
                            print(f"Error deleting message from SQS: {delete_error}")

                        return response_body.get("result", "")

        except Exception as e:
            print(f"Error polling SQS: {e}")
            return None

    return {"error": "Timeout waiting for response from Face Recognition"}

def send_request(image_path):
    """Send a request to Face Detection Lambda **synchronously**."""
    global passed_requests, failed_requests

    with open(image_path, "rb") as f:
        encoded_file = base64.b64encode(f.read()).decode("utf-8")

    request_id  = str(uuid.uuid4())
    payload     = json.dumps({"request_id": request_id, "content": encoded_file, "filename": image_path})
    headers     = {"Content-Type": "application/json"}

    try:
        response = requests.post(lambda_url, data=payload, headers=headers)

        if response.status_code != 200:
            print(f"Failed request {request_id}: {response.url}")
            failed_requests += 1
            return None, None
        else:
            #print(f"Request {request_id} sent for {os.path.basename(image_path)}")
            passed_requests += 1
            filename = image_path.split('/')[-1]
            return request_id, filename

    except Exception as err:
        print(f"Exception while sending request: {err}")
        failed_requests += 1
        return None, None


def send_one_request(image_path):
    """Sends a request and updates counters"""
    global sqs, response_queue_url, correct_predictions, wrong_predictions, active_requests, prediction_df

    with lock:
        # Increment active request count
        active_requests += 1

    try:
        request_id, filename = send_request(image_path)
        if request_id and filename:
            result = poll_response(sqs, request_id, response_queue_url)
            if result:
                # Compare with ground truth
                #print(f"filename: {filename}")
                ground_truth = prediction_df.loc[prediction_df['Image'] == filename, 'Results'].values[0]
                if ground_truth.strip() == result:
                    correct_predictions += 1
                else:
                    wrong_predictions += 1

    finally:
        with lock:
            active_requests -= 1  # Decrement active request count
            if active_requests == 0 and image_index >= num_request:
                dump_statistics()

def workload_scheduler():
    """Schedules requests using a timer, launching a new thread for each request."""
    global image_index

    with lock:
        if image_index >= num_request:
            if active_requests == 0:
                # All requests sent & processed
                dump_statistics()
            return

        image_path = image_path_list[image_index % len(image_path_list)]
        image_index += 1

    threading.Thread(target=send_one_request, args=(image_path,)).start()
    threading.Timer(timer_interval, workload_scheduler).start()

def dump_statistics():
    total_duration = time.time() - start_time

    print("Workload complete! Dumping statistics...")

    print (f"[Workload-gen] ----- Workload Generator Statistics -----")
    print (f"[Workload-gen] Total number of requests: {num_request}")
    print (f"[Workload-gen] Total number of requests completed successfully: {passed_requests}")
    print (f"[Workload-gen] Total number of failed requests: {failed_requests}")
    print (f"[Workload-gen] Total number of correct predictions : {correct_predictions}")
    print (f"[Workload-gen] Total number of wrong predictions: {wrong_predictions}")
    print (f"[Workload-gen] Total test duration: {total_duration} (seconds)")
    print (f"[Workload-gen] ------------------------------------------")


# Start the timer-based workload scheduler
print(f" Starting workload generator... Sending {num_request} requests with timer interval {timer_interval} seconds")

start_time = time.time()
workload_scheduler()
