__copyright__   = "Copyright 2024, VISA Lab"
__license__     = "MIT"

import sys
import os
import time
import _thread
import argparse
import requests
import subprocess
import numpy as np
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

parser = argparse.ArgumentParser(description='Upload images')
parser.add_argument('--num_request', type=int, help='one image per request')
parser.add_argument('--ip_addr', type=str, help='IP address of the web tier')
parser.add_argument('--image_folder', type=str, help='the path of the folder where images are saved')
parser.add_argument('--prediction_file', type=str, help='the path of the classification results file')
args = parser.parse_args()

num_request     = args.num_request
url             = f"http://{args.ip_addr}:8000/"
image_folder    = args.image_folder
prediction_file = args.prediction_file
prediction_df   = pd.read_csv(prediction_file)
responses       = 0
err_responses   = 0
correct_predictions = 0
wrong_predictions   = 0
ex_requests         = []

def send_one_request(image_path):
    global prediction_df, responses, err_responses, correct_predictions, wrong_predictions, ex_requests
    # Define http payload, "myfile" is the key of the http payload
    file = {"inputFile": open(image_path,'rb')}
    try:
        response = requests.post(url, files=file)
        # Print error message if failed
        if response.status_code != 200:
            print('sendErr: '+response.url)
            err_responses +=1
        else :
            filename    = os.path.basename(image_path)
            image_msg   = filename + ' uploaded!'
            msg         = image_msg + '\n' + 'Classification result: ' + response.text
            #print(f"[Workload-gen] {msg}")
            responses   +=1
            correct_result = prediction_df.loc[prediction_df['Image'] == filename.split('.')[0], 'Results'].iloc[0]
            if correct_result.strip() == response.text.split(':')[1].strip():
                correct_predictions +=1
            else:
                wrong_predictions +=1
    except requests.exceptions.RequestException as errex:
        print("Exception:", errex)
        ex_requests.append(image_path)

num_max_workers = 100
image_path_list = []
test_start_time = time.time()

for i, name in enumerate(os.listdir(image_folder)):
    if i == num_request:
        break
    image_path_list.append(os.path.join(image_folder,name))

with ThreadPoolExecutor(max_workers = num_max_workers) as executor:
    executor.map(send_one_request, image_path_list)

print(f"[Workload-gen] Attempt-1 {responses}/{num_request} requests successful.")

# Retry requests until all requests are successful or ex_requests is empty
retry_attempt=2
while ex_requests:
    retry_requests = ex_requests.copy()
    ex_requests.clear()
    with ThreadPoolExecutor(max_workers=num_max_workers) as executor:
        executor.map(send_one_request, retry_requests)
    print(f"[Workload-gen] Attempt-{retry_attempt} {responses}/{num_request} requests successful.")
    retry_attempt += 1

test_duration = time.time() - test_start_time
print("[Workload-gen] All requests have been processed or retried.")

if num_request == (responses + err_responses):
   print (f"[Workload-gen] ----- Workload Generator Statistics -----")
   print (f"[Workload-gen] Total number of requests: {num_request}")
   print (f"[Workload-gen] Total number of requests completed successfully: {responses}")
   print (f"[Workload-gen] Total number of failed requests: {err_responses}")
   print (f"[Workload-gen] Total number of correct predictions : {correct_predictions}")
   print (f"[Workload-gen] Total number of wrong predictions: {wrong_predictions}")
   print (f"[Workload-gen] Total Test Duration: {test_duration} (seconds)")
   print (f"[Workload-gen] -----------------------------------")
