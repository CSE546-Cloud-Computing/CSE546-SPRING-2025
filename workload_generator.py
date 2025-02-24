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
passed_requests     = 0
failed_requests     = 0
correct_predictions = 0
wrong_predictions   = 0

def send_one_request(image_path):
    global prediction_df, passed_requests, failed_requests, correct_predictions, wrong_predictions
    # Define http payload, "myfile" is the key of the http payload
    file = {"inputFile": open(image_path,'rb')}
    try:
        response = requests.post(url, files=file)
        # Print error message if failed
        if response.status_code != 200:
            print('sendErr: '+response.url)
            failed_requests +=1
        else :
            filename    = os.path.basename(image_path)
            image_msg   = filename + ' uploaded!'
            msg         = image_msg + '\n' + 'Classification result: ' + response.text
            #print(f"[Workload-gen] {msg}")
            passed_requests   +=1
            correct_result = prediction_df.loc[prediction_df['Image'] == filename.split('.')[0], 'Results'].iloc[0]
            if correct_result.strip() == response.text.split(':')[1].strip():
                correct_predictions +=1
            else:
                wrong_predictions +=1
    except (requests.exceptions.RequestException, Exception) as errex:
        print("Exception:", errex)
        failed_requests +=1

num_max_workers = 100
image_path_list = []
test_start_time = time.time()

for i, name in enumerate(os.listdir(image_folder)):
    if i == num_request:
        break
    image_path_list.append(os.path.join(image_folder,name))

with ThreadPoolExecutor(max_workers = num_max_workers) as executor:
    executor.map(send_one_request, image_path_list)

test_duration = time.time() - test_start_time

print (f"[Workload-gen] ----- Workload Generator Statistics -----")
print (f"[Workload-gen] Total number of requests: {num_request}")
print (f"[Workload-gen] Total number of requests completed successfully: {passed_requests}")
print (f"[Workload-gen] Total number of failed requests: {failed_requests}")
print (f"[Workload-gen] Total number of correct predictions : {correct_predictions}")
print (f"[Workload-gen] Total number of wrong predictions: {wrong_predictions}")
print (f"[Workload-gen] Total response time: {test_duration} (seconds)")
print (f"[Workload-gen] -----------------------------------")
