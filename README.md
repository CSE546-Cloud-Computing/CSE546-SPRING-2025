# Autograder for Project 2 Part 2

Make sure that you use the provided autograder and follow the instructions below to test your project submission. Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.

- Download the zip file you submitted from Canvas. 
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - `cd CSE546-SPRING-2025/`
  - `git checkout project-2-part-2`
- Create a directory `submissions` in the CSE546-SPRING-2025 directory and move your zip file to the submissions directory.

## Run the autograder
- To run the autograder (without the bonus requirement): ```python3 autograder.py --num_requests 100 --img_folder="<dataset folder path>" --pred_file="<output classification csv file path>"```
- The autograder will look for submissions for each entry present in the class_roster.csv
- For each submission the autograder will
  - The autograder extracts the credentials.txt from the submission and parses the entries.
  - Use the Grader IAM credentials to test the project as per the grading rubrics and allocate grade points.
- The autograder has a workload generator component to publish messages to the MQTT topic to which your face-detection component subscribes.
- In the score of this project the workload generator will be executed on the IoT Client device (IoT-Greengrass-Client) and the autograder will take care of this.
- You just need to make sure all the dependencies are installed on the IoT client EC2 instance.
- Install the dependencies: boto3, pandas, awscrt, and awsiot.
  - Install them using the command: `pip3 install boto3, pandas, awscrt`
  - ```python3 -m pip install awsiotsdk```


## Sample Output
Note: In the below sample output some portion logs of zip and unzip are trimmed in order to save space and maintain readability.

```
+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
- 1) Extract the credentials from the credentials.txt
- 2) Execute the test cases as per the Grading Rubrics
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
Project Path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-2/grader
Grade Project: Project-2
Class Roster: class_roster.csv
Zip folder path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-2/grader/submissions
Grading script: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-2/grader/grade_project2_p1.py
Test Image folder path: ../../datasets/frames
Classification results file: ../../datasets/FaceRecognitionResults.csv
Autograder Results: Project-2-grades.csv
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ Grading for Doe John ASUID: 1225754101 +++++++++++++++++++++
Extracted /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-2/grader/submissions/Project2-1225754101.zip to extracted
File: extracted/credentials/credentials.txt has values ('XXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXX', 'X.XX.XX.XX', 'https://sqs.us-east-1.amazonaws.com/XXXXXXXXX/1225754101-resp-queue-fifo.fifo')
Credentials parsing complete.
-----------------------------------------------------------------
IAM ACCESS KEY ID: XXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXX
-----------------------------------------------------------------
Following policies are attached with IAM user:cse546-AutoGrader: ['AWSGreengrassReadOnlyAccess', 'AWSIoTFullAccess', 'AmazonEC2ReadOnlyAccess', 'IAMReadOnlyAccess', 'AmazonSQSFullAccess', 'AWSLambda_ReadOnlyAccess']
[IAM-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[IAM-log] AmazonSQSFullAccess policy attached with grading IAM
[IAM-log] AWSLambda_ReadOnlyAccess policy attached with grading IAM
[IAM-log] AWSGreengrassReadOnlyAccess policy attached with grading IAM
[Cloudwatch-log] Alarm:Billing-alarm-5$ with ARN:arn:aws:cloudwatch:us-east-1:XXXXXXXXX:alarm:Billing-alarm-5$ found in state:ALARM. It is configued with statistic:Maximum, threshold:5.0 and Comparison Operator:GreaterThanOrEqualToThreshold
[Cloudwatch-log] CAUTION !!! Billing alarm:arn:aws:cloudwatch:us-east-1:XXXXXXXXX:alarm:Billing-alarm-5$ is triggered. Release the unwanted resources
[Cloudwatch-log] CAUTION !! You do not have a Cloudwatch alarm set. Kindly refer to the Project-0 document and learn how to set a billing alarm
-------------- CSE546 Cloud Computing Grading Console -----------
IAM ACCESS KEY ID: XXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXX
Elastic IPv4 address of IoT-Greengrass-Client :X.XX.XX.XX
SQS Response Queue URL: https://sqs.us-east-1.amazonaws.com/XXXXXXXXX/1225754101-resp-queue-fifo.fifo
-----------------------------------------------------------------
----------------- Executing Test-Case:1 ----------------
[EC2-log] IoT Greengrass Core and client validation Pass. Found 1 IoT-Greengrass-Core instance in running state. Found 1 IoT-Greengrass-Client instance in running state.Points deducted: 0
[IoT-log] Found a IoT Core Device: GreengrassQuickStartCore-195585ade54 with state HEALTHY.
[IoT-log] Found a component com.clientdevices.FaceDetection in RUNNING state.
[IoT-log] 1225754101-IoTThing found. Points deducted: 0
[Lambda-log] The function: face-recognition-part-1 exists.
[Lambda-log] ---------------------------------------------------------
[SQS-log] The expectation is that both the Request and Response SQS should exist and be EMPTY
[SQS-log] - WARN: This will purge any messages available in the SQS
[SQS-log] ---------------------------------------------------------
[SQS-log] SQS Request Queue:1225754101-req-queue has 0 pending messages.
[SQS-log] SQS Response Queue:1225754101-resp-queue has 0 pending messages.
[SQS-log] Points deducted:0
----------------- Executing Test-Case:2 ----------------
  adding: 1225754101_grading/ (stored 0%)
  adding: 1225754101_grading/CSE546-SPRING-2025/ (stored 0%)
  adding: 1225754101_grading/CSE546-SPRING-2025/.git/ (stored 0%)
  ....
  ....
  adding: 1225754101_grading/CSE546-SPRING-2025/FaceRecognitionResults.csv (deflated 82%)
  adding: 1225754101_grading/CSE546-SPRING-2025/workload_generator.py (deflated 66%)
  adding: 1225754101_grading/CSE546-SPRING-2025/1225754101_exec.sh (deflated 44%)
  adding: 1225754101_grading/CSE546-SPRING-2025/command_line_utils.py (deflated 89%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/ (stored 0%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_67.jpg (deflated 6%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_90.jpg (deflated 1%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_36.jpg (deflated 7%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_51.jpg (deflated 6%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_27.jpg (deflated 6%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_73.jpg (deflated 1%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_17.jpg (deflated 1%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_24.jpg (deflated 1%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_71.jpg (deflated 8%)
  adding: 1225754101_grading/CSE546-SPRING-2025/frames/test_96.jpg (deflated 1%)
  ....
  ....
  (Last message repeated 90 times)
 Creating the testing package ...
 -- Git clone Project-2 Part-2
 -- Generate the test script file
Shell script '1225754101_exec.sh' generated successfully!
 -- Move the test package to the IoT-Greengrass-Client ...
 -- ssh connect to the IoT-Greengrass-Client : X.XX.XX.XX
 -- Execute the workload generator on the IoT-Greengrass-Client : X.XX.XX.XX
Archive:  1225754101_grading.zip
   creating: 1225754101_grading/
   creating: 1225754101_grading/CSE546-SPRING-2025/
   creating: 1225754101_grading/CSE546-SPRING-2025/.git/
   ...
   ...
  inflating: 1225754101_grading/CSE546-SPRING-2025/FaceRecognitionResults.csv
  inflating: 1225754101_grading/CSE546-SPRING-2025/workload_generator.py
  inflating: 1225754101_grading/CSE546-SPRING-2025/1225754101_exec.sh
  inflating: 1225754101_grading/CSE546-SPRING-2025/command_line_utils.py
   creating: 1225754101_grading/CSE546-SPRING-2025/frames/
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_67.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_90.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_36.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_96.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_84.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_01.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_87.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_09.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_47.jpg
  inflating: 1225754101_grading/CSE546-SPRING-2025/frames/test_21.jpg
  ....
  ....
  (Last message repeated 90 times)
  inflating: 1225754101_grading/CSE546-SPRING-2025/README.md
Performing greengrass discovery... on thing IOT-client-workload-gen
awsiot.greengrass_discovery.DiscoverResponse(gg_groups=[awsiot.greengrass_discovery.GGGroup(gg_group_id='greengrassV2-coreDevice-GreengrassQuickStartCore-195585ade54', cores=[awsiot.greengrass_discovery.GGCore(thing_arn='arn:aws:iot:us-east-1:XXXXXXXXX:thing/GreengrassQuickStartCore-195585ade54', connectivity=[awsiot.greengrass_discovery.ConnectivityInfo(id='172.31.82.115', host_address='172.31.82.115', metadata='', port=8883)])], certificate_authorities=['-----BEGIN
CERTIFICATE-----\nabcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwx
yzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcde
fghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedO
verThelazyDog\abcdefghijklmnopqrstuvwxyzAquickBrownFoxJumpedOverThelazyDog\n-----END CERTIFICATE-----\n'])])
Trying core arn:aws:iot:us-east-1:XXXXXXXXX:thing/GreengrassQuickStartCore-195585ade54 at host 172.31.82.115 port 8883
Connected!
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
Publish received on topic clients/1225754101-IoTThing
....
....
(Last message repeated 90 times)
MQTT publishing completed ...
Polling thread stopping ...
Workload complete! Dumping statistics...
[Workload-gen] ----- Workload Generator Statistics -----
[Workload-gen] Total number of requests: 100
[Workload-gen] Total number of requests completed successfully: 100
[Workload-gen] Total number of failed requests: 0
[Workload-gen] Total number of correct predictions : 100
[Workload-gen] Total number of wrong predictions: 0
[Workload-gen] Total test duration: 77.5672435760498 (seconds)
[Workload-gen] ------------------------------------------
 -- starting remote cleanup ..
 -- starting local cleanup ..
[Test-Case-3-log] 100/100 completed successfully.Points:[20.0/20]
[Test-Case-3-log] 100/100 correct predictions.Points:[20.0/20]
[Test-Case-3-log] Test Average Latency: 0.775672435760498 sec. `avg latency<2.5s`.Points:[60/60]
[Test-Case-3-log] ---------------------------------------------------------
Total Grade Points: 100.0
Removed extracted folder: extracted
Total time taken to grade for Doe John ASUID: 1225754101: 331.48881125450134 seconds
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Grading complete for Project-2. Check the Project-2-grades.csv file.

```
