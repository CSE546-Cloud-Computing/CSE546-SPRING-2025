
import re
import os
import pdb
import time
import shutil
import argparse
import paramiko

parser = argparse.ArgumentParser(description='Upload images')
parser.add_argument('--asu_id', type=str, help='ASU ID of the test student')
parser.add_argument('--ip_addr', type=str, help='IP address of the IoT client')
parser.add_argument('--pem', type=str, help='pem file path')
parser.add_argument('--max_pub_ops', type=int, help="number of messages to be published")
parser.add_argument('--image_folder', type=str, help='dataset folder path')
parser.add_argument('--prediction_file', type=str, help='prediction file path')
parser.add_argument('--response_queue_url', type=str, help='SQS response queue URL')

args                = parser.parse_args()
asu_id              = args.asu_id
ip_addr             = args.ip_addr
pem_file_path       = args.pem
max_pub_ops         = args.max_pub_ops
image_folder        = args.image_folder
prediction_file     = args.prediction_file
response_queue_url  = args.response_queue_url

private_key = paramiko.RSAKey.from_private_key_file(pem_file_path)
ssh_client  = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def generate_sh_file(asuid, max_pub_ops, response_queue_url, image_folder, prediction_file):
    filename    = f"{asu_id}_exec.sh"
    file_path   = f"{asu_id}_grading/CSE546-SPRING-2025/{filename}"

    thing_name  = f"{asu_id}-IoTThing"
    topic       = f"clients/{asu_id}-IoTThing"

    ca_file     = f"$HOME/{asu_id}-certs/AmazonRootCA1.pem"
    cert_file   = f"$HOME/{asu_id}-certs/device.pem.crt"
    key_file    = f"$HOME/{asu_id}-certs/private.pem.key"
    region      = "us-east-1"

    content     = f"""#!/bin/bash

set -x

python3 workload_generator.py \\
    --max_pub_ops {max_pub_ops} \\
    --response_queue_url "{response_queue_url}" \\
    --image_folder "{image_folder}" \\
    --prediction_file "{prediction_file}" \\
    --thing_name "{thing_name}" \\
    --topic "{topic}" \\
    --ca_file "{ca_file}" \\
    --cert "{cert_file}" \\
    --key "{key_file}" \\
    --region {region} \\
    --verbosity Warn
"""

    with open(file_path, 'w') as f:
        f.write(content)
    print(f"Shell script '{filename}' generated successfully!")


try:

    print(f"Creating the testing package ...")
    os.makedirs(f"./{asu_id}_grading", exist_ok=True)

    pred_file_name      = prediction_file.split('/')[-1]
    dataset_folder_name = image_folder.split('/')[-1]

    git_clone_cmd       = f"cd ./{asu_id}_grading && git clone -b project-2-part-2 git@github.com:CSE546-Cloud-Computing/CSE546-SPRING-2025.git && cd .."
    code_path           = f"{asu_id}_grading/CSE546-SPRING-2025"
    sh_filename         = f"{asu_id}_exec.sh"
    sh_file_path        = f"{code_path}/{sh_filename}"

    prediction_cp_cmd   = f"cp {prediction_file} {code_path}"
    dataset_cp_cmd      = f"cp -r {image_folder} {code_path}"
    dataset_zip_cmd     = f"zip -r {code_path}/{dataset_folder_name}.zip {image_folder}"
    zip_cmd             = f"zip -r {asu_id}_grading.zip ./{asu_id}_grading/"
    init_workload_cmd   = f"unzip {asu_id}_grading.zip && cd {asu_id}_grading/CSE546-SPRING-2025 && bash {asu_id}_exec.sh"
    #init_workload_cmd   = f"cd {asu_id}_grading/CSE546-SPRING-2025 && bash {asu_id}_exec.sh"
    iot_cli_scp_cmd     = f"scp -i {pem_file_path} {asu_id}_grading.zip ubuntu@{ip_addr}:~/"
    pem_permission_cmd  = f"chmod 600 {pem_file_path}"
    sh_permission_cmd   = f"chmod +x {sh_file_path}"
    username            = "ubuntu"
    cleanup_cmd         = f"rm -rf ./{asu_id}_grading && rm {asu_id}_grading.zip"


    print(f" -- Git clone Project-2 Part-2")
    os.system(git_clone_cmd)
    os.system(prediction_cp_cmd)
    os.system(dataset_cp_cmd)

    print(f" -- Generate the test script file")

    generate_sh_file(asu_id, max_pub_ops, response_queue_url, f"./{dataset_folder_name}", f"./{pred_file_name}")

    os.system(pem_permission_cmd)
    os.system(sh_permission_cmd)
    os.system(zip_cmd)

    print(" -- Move the test package to the IoT-Greengrass-Client ...")
    os.system(iot_cli_scp_cmd)

    print(f" -- ssh connect to the IoT-Greengrass-Client : {ip_addr}")

    ssh_client.connect(hostname=ip_addr, username=username, pkey=private_key)

    print(f" -- Execute the workload generator on the IoT-Greengrass-Client : {ip_addr}")

    stdin, stdout, stderr = ssh_client.exec_command(init_workload_cmd)
    full_output = ""

    while True:
        if stdout.channel.recv_ready():
            chunk = stdout.channel.recv(4096).decode()
            print(chunk, end="")
            full_output += chunk

        if stdout.channel.exit_status_ready():
            break
        time.sleep(0.1)

    exit_status     = stdout.channel.recv_exit_status()
    error_output    = stderr.read().decode()

    print(f" -- starting remote cleanup ..")
    stdin, stdout, stderr = ssh_client.exec_command(cleanup_cmd)
    ssh_client.close()

    print(f" -- starting local cleanup ..")
    shutil.rmtree(f"./{asu_id}_grading")
    os.remove(f"{asu_id}_grading.zip")

    #return full_output
except Exception as e:
    print (e)
