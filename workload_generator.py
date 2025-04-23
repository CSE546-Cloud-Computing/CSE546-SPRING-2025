__copyright__   = "Copyright 2025, VISA Lab"
__license__     = "MIT"

import os
import pdb
import time
import uuid
import json
import boto3
import base64
import random
import tempfile
import argparse
import threading
import io as cse_io
import pandas as pd
from PIL import Image
from awscrt import io, http
from awscrt.mqtt import QoS
from awsiot import mqtt_connection_builder
from concurrent.futures import ThreadPoolExecutor
from awsiot.greengrass_discovery import DiscoveryClient

from command_line_utils import CommandLineUtils

allowed_actions = ['both', 'publish', 'subscribe']
cmdData         = CommandLineUtils.parse_sample_input_basic_discovery()
polling_data    = {}
publish_data    = {}
stop_event      = threading.Event()
prediction_df   = pd.read_csv(cmdData.input_prediction_file)
image_path_list = [os.path.join(cmdData.input_image_folder, f) for f in os.listdir(cmdData.input_image_folder) if f.endswith((".jpg", ".png"))]
tls_options     = io.TlsContextOptions.create_client_with_mtls_from_path(cmdData.input_cert, cmdData.input_key)

if (cmdData.input_ca is not None):
    tls_options.override_default_trust_store_from_path(None, cmdData.input_ca)
tls_context = io.ClientTlsContext(tls_options)

socket_options  = io.SocketOptions()
proxy_options   = None
if cmdData.input_proxy_host is not None and cmdData.input_proxy_port != 0:
    proxy_options = http.HttpProxyOptions(cmdData.input_proxy_host, cmdData.input_proxy_port)

print(f'Performing greengrass discovery... on thing {cmdData.input_thing_name}')
#print(f"cert_path: {cmdData.input_cert}")
#print(f"key path: {cmdData.input_key}")
#print(f"ca_path: {cmdData.input_ca}")

discovery_client = DiscoveryClient(
    io.ClientBootstrap.get_or_create_static_default(),
    socket_options,
    tls_context,
    cmdData.input_signing_region, None, proxy_options)

resp_future         = discovery_client.discover(cmdData.input_thing_name)
discover_response   = resp_future.result()

if (cmdData.input_is_ci):
    print("Received a greengrass discovery result! Not showing result in CI for possible data sensitivity.")
else:
    print(discover_response)

if (cmdData.input_print_discovery_resp_only):
    exit(0)

def on_connection_interupted(connection, error, **kwargs):
    print('connection interrupted with error {}'.format(error))

def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print('connection resumed with return code {}, session present {}'.format(return_code, session_present))

def establish_mqtt_connection():
    for gg_group in discover_response.gg_groups:
        for gg_core in gg_group.cores:
            for connectivity_info in gg_core.connectivity:
                try:
                    print(
                        f"Trying core {gg_core.thing_arn} at host {connectivity_info.host_address} port {connectivity_info.port}")
                    mqtt_connection = mqtt_connection_builder.mtls_from_path(
                        endpoint=connectivity_info.host_address,
                        port=connectivity_info.port,
                        cert_filepath=cmdData.input_cert,
                        pri_key_filepath=cmdData.input_key,
                        ca_bytes=gg_group.certificate_authorities[0].encode('utf-8'),
                        on_connection_interrupted=on_connection_interupted,
                        on_connection_resumed=on_connection_resumed,
                        client_id=cmdData.input_thing_name,
                        clean_session=False,
                        keep_alive_secs=30)

                    connect_future = mqtt_connection.connect()
                    connect_future.result()
                    print('Connected!')
                    return mqtt_connection

                except Exception as e:
                    print('Connection failed with exception {}'.format(e))
                    continue

    exit('All connection attempts failed')


mqtt_connection = establish_mqtt_connection()

if cmdData.input_mode == 'both' or cmdData.input_mode == 'subscribe':
    def on_publish(topic, payload, dup, qos, retain, **kwargs):
        print('Publish received on topic {}'.format(topic))
        #print(payload)
    subscribe_future, _ = mqtt_connection.subscribe(cmdData.input_topic, QoS.AT_MOST_ONCE, on_publish)
    subscribe_result    = subscribe_future.result()

def poll_sqs():

	response_queue_url 	= cmdData.input_response_queue_url
	sqs_client 			= boto3.client('sqs', 'us-east-1')

	while not stop_event.is_set():
		response = sqs_client.receive_message(
				QueueUrl=response_queue_url,
				AttributeNames=['All'],
				MaxNumberOfMessages=1,
				WaitTimeSeconds=10
				)

		if 'Messages' in response:
			for message in response['Messages']:
				receipt_handle  = message['ReceiptHandle']
				response_body   = json.loads(message['Body'])
				#print(f"Response body: {response_body}")
				request_id      = response_body.get('request_id')
				result          = response_body.get('result')
				if request_id:
					polling_data[request_id] =  {'resp_ack_time': time.time(), 'result': result}

				# Delete the message from the queue after processing
				sqs_client.delete_message(
						QueueUrl=response_queue_url,
						ReceiptHandle=receipt_handle
						)
			#print(f"Received and processed response for request_id={request_id}")

		time.sleep(1)

	print("Polling thread stopping ...")

def collate_results():
    global cmdData, publish_data, polling_data
    passed_requests     = 0
    failed_requests     = 0
    correct_predictions = 0
    wrong_predictions   = 0
    total_duration		= 0

    for request_id, publish_info in publish_data.items():
        ground_truth    = publish_info['ground_truth']
        pub_time        = publish_info['pub_time']

        if request_id in polling_data:
            passed_requests += 1

            polling_info    = polling_data[request_id]
            result          = polling_info['result']
            resp_ack_time   = polling_info['resp_ack_time']

            is_correct      = (ground_truth == result)
            #print(f"[GT:{ground_truth}] Results:{result}")
            latency_per_req = resp_ack_time - pub_time
            total_duration += latency_per_req

            if is_correct:
                correct_predictions +=1
            else:
                wrong_predictions += 1

        else:
            failed_requests += 1
            print(f"[Warning] No response found for Request ID: {request_id}\n")

    print("Workload complete! Dumping statistics...")
    print (f"[Workload-gen] ----- Workload Generator Statistics -----")
    print (f"[Workload-gen] Total number of requests: {cmdData.input_max_pub_ops}")
    print (f"[Workload-gen] Total number of requests completed successfully: {passed_requests}")
    print (f"[Workload-gen] Total number of failed requests: {failed_requests}")
    print (f"[Workload-gen] Total number of correct predictions : {correct_predictions}")
    print (f"[Workload-gen] Total number of wrong predictions: {wrong_predictions}")
    print (f"[Workload-gen] Total test duration: {total_duration} (seconds)")
    print (f"[Workload-gen] ------------------------------------------")

def publish_requests():
    global image_path_list, num_request, mqtt_connection, cmdData, publish_data, prediction_df

    random.seed(42)
    random.shuffle(image_path_list)

    loop_count  = 0
    max_pub_ops = cmdData.input_max_pub_ops

    while loop_count < max_pub_ops:
        request_id  = str(uuid.uuid4())
        image_path  = image_path_list[loop_count]
        filename    = image_path.split('/')[-1]

        with Image.open(image_path) as img:
            img 	= img.resize((512, 512))
            buffer 	= cse_io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)
            encoded_file = base64.b64encode(buffer.read()).decode("utf-8")

        message = {
                'request_id':   request_id,
                'sequence':     loop_count,
                'filename':     filename,
                'encoded':      encoded_file
                }

        messageJson   = json.dumps(message)
        #pub_future, _ = mqtt_connection.publish(cmdData.input_topic, messageJson, QoS.AT_LEAST_ONCE)
        pub_future, _ = mqtt_connection.publish(cmdData.input_topic, messageJson, QoS.AT_MOST_ONCE)

        ground_truth = prediction_df.loc[prediction_df['Image'] == filename, 'Results'].values[0]
        publish_data[request_id] = {'ground_truth':ground_truth, 'pub_time':time.time()}
        #pub_future.result(timeout=10)  # Wait for publish to complete

        #print(f"Published message with request_id={request_id}")

        time.sleep(2)
        loop_count += 1

    print("MQTT publishing completed ...")
    stop_event.set()

polling_thread = threading.Thread(target=poll_sqs, daemon=True)
polling_thread.start()

publish_requests()
polling_thread.join()

collate_results()
