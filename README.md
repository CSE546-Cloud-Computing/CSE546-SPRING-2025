# Autograder for Project-1 Part 2

Make sure that you use the provided autograder and follow the instructions below to test your project submission. Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.

- Download the zip file you submitted from Canvas. 
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - `cd CSE546-SPRING-2025/`
  - `git checkout project-1-part-2`
- Create a directory `submissions` in the CSE546-SPRING-2025 directory and move your zip file to the submissions directory.

## Prepare to run the autograder
- Install Python: `sudo apt install python3`
- Populate the `class_roster.csv`
  - If you are a student; replace the given template only with your details.
  - If you are a grader; use the class roster for the entire class

## Run the autograder
- Run the autograder: `python3 autograder.py --num_requests 100 --img_folder="<dataset folder path>" --pred_file="<output classification csv file path>"`
  ```
  python3 autograder.py --help
  usage: autograder.py [-h] [--img_folder IMG_FOLDER] [--pred_file PRED_FILE] [--num_requests NUM_REQUESTS]
  Upload images
  options:
  -h, --help            show this help message and exit
  --num_requests NUM_REQUESTS  Number of Requests
  --img_folder IMG_FOLDER Path to the input images
  --pred_file PRED_FILE Classfication results file
  ```
- The autograder will look for submissions for each entry present in the class_roster.csv
  - For each submission the autograder will
  - The autograder extracts the credentials.txt from the submission and parses the entries.
  - Use the Grader IAM credentials to test the project as per the grading rubrics and allocate grade points.
  - The autograder has a workload generator component to generate requests to your web tier.
  - The autograder will dump stdout and stderr in a log file named `autograder.log`
      
## Sample Output

```
  +++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
- 1) Extract the credentials from the credentials.txt
- 2) Execute the test cases as per the Grading Rubrics
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
Project Path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-1/part-2/grader
Grade Project: Project-1
Class Roster: class_roster.csv
Zip folder path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-1/part-2/grader/submissions
Grading script: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-1/part-2/grader/grade_project1_p2.py
Test Image folder path: ../web-tier/upload_images/
Classification results file: ../../Classification Results on Face Dataset (1000 images).csv
Autograder Results: Project-1-grades.csv
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ Grading for Doe John ASUID: 1225754101 +++++++++++++++++++++
Extracted /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-1/part-2/grader/submissions/Project1-1225754101.zip to extracted
File: extracted/credentials/credentials.txt has values (‘XXXXXXXXXXXXXXXXXX’, ‘XXXXXXXXXXXXXXXXXX’, 'XXXXXX')
Credentials parsing complete.
-----------------------------------------------------------------
IAM ACCESS KEY ID: XXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY:XXXXXXXXXXXXXXXXXX
-----------------------------------------------------------------
Following policies are attached with IAM user:cse546-AutoGrader: ['AmazonEC2ReadOnlyAccess', 'IAMReadOnlyAccess', 'AmazonSQSFullAccess', 'AmazonS3FullAccess']
[IAM-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[IAM-log] AmazonS3FullAccess policy attached with grading IAM
[IAM-log] AmazonSQSFullAccess policy attached with grading IAM
[Cloudwatch-log] CAUTION !! You do not have a Cloudwatch alarm set. Kindly refer to the Project-0 document and learn how to set a billing alarm
-------------- CSE546 Cloud Computing Grading Console -----------
IAM ACCESS KEY ID: XXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY:XXXXXXXXXXXXXXXXXX
Web-Instance IP Address: XXXXXX
-----------------------------------------------------------------
----------------- Executing Test-Case:1 ----------------
[EC2-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[EC2-log] Found 1 web-tier instances in running state.
[EC2-log] Found 0 app-tier instances in running state
[EC2-log] EC2-state validation Pass. Found 1 web-tier instances in running state. Found 0 app-tier instances in running state.Points deducted: 0
[S3-log] AmazonS3FullAccess policy attached with grading IAM
[S3-log] - WARN: If there are objects in the S3 buckets; they will be deleted
[S3-log] ---------------------------------------------------------
[S3-log] S3 Bucket:1225754101-in-bucket has 0 object(s).
[S3-log] S3 Bucket:1225754101-out-bucket has 0 object(s).
[S3-log] Points deducted:0
[SQS-log] The expectation is that both the Request and Response Queues should exist with max message size set to 1KB and be EMPTY
[SQS-log] - WARN: This will purge any messages available in the SQS
[SQS-log] ---------------------------------------------------------
[SQS-log] AmazonSQSFullAccess policy attached with grading IAM
[SQS-log] SQS Request Queue:1225754101-req-queue has 0 pending messages with max message size set to 1 KB.
[SQS-log] SQS Response Queue:1225754101-resp-queue has 0 pending messages.
[SQS-log] Points deducted:0
----------------- Executing Test-Case:2 ----------------
[AS-log] - Autoscaling validation starts ..
[AS-log] - The expectation is as follows:
[AS-log]  -- # of app tier instances should gradually scale and eventually reduce back to 0
[AS-log]  -- # of SQS messages should gradually increase and eventually reduce back to 0
------------------------------------------------------------------------------------------------------------------
|   # of messages in   |   # of messages in   |   # of app-tier EC2  |  # of objects in S3  |  # of objects in S3  |
|  SQS Request Queue   |  SQS Response Queue  | instances in running |     Input Bucket     |     Output Bucket    
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |          0           |          0           |
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |          0           |          0           |
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |          0           |          0           |
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |          0           |          0           |
------------------------------------------------------------------------------------------------------------------
|          29          |          0           |          0           |          47          |          0           |
------------------------------------------------------------------------------------------------------------------
|          29          |          0           |          0           |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|          78          |          0           |          0           |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|          78          |          0           |          0           |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          2           |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          6           |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          12          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|          29          |          0           |          15          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          15          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          15          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          15          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|          99          |          0           |          15          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|         100          |          0           |          15          |         100          |          0           |
------------------------------------------------------------------------------------------------------------------
|          87          |          0           |          15          |         100          |          2           |
------------------------------------------------------------------------------------------------------------------
|          97          |          0           |          15          |         100          |          6           |
------------------------------------------------------------------------------------------------------------------
|          91          |          0           |          15          |         100          |          10          |
------------------------------------------------------------------------------------------------------------------
|          73          |          0           |          15          |         100          |          16          |
------------------------------------------------------------------------------------------------------------------
|          75          |          2           |          15          |         100          |          25          |
------------------------------------------------------------------------------------------------------------------
|          87          |          0           |          15          |         100          |          33          |
------------------------------------------------------------------------------------------------------------------
|          54          |          4           |          15          |         100          |          43          |
------------------------------------------------------------------------------------------------------------------
|          39          |          4           |          15          |         100          |          51          |
------------------------------------------------------------------------------------------------------------------
|          70          |          12          |          15          |         100          |          62          |
------------------------------------------------------------------------------------------------------------------
|          54          |          0           |          15          |         100          |          71          |
------------------------------------------------------------------------------------------------------------------
|          30          |          0           |          15          |         100          |          81          |
------------------------------------------------------------------------------------------------------------------
|          16          |          14          |          15          |         100          |          91          |
------------------------------------------------------------------------------------------------------------------
|          0           |          12          |          15          |         100          |          97          |
------------------------------------------------------------------------------------------------------------------
|          61          |          9           |          15          |         100          |          97          |
------------------------------------------------------------------------------------------------------------------
|          73          |          10          |          15          |         100          |          98          |
------------------------------------------------------------------------------------------------------------------
|          5           |          12          |          15          |         100          |          98          |
------------------------------------------------------------------------------------------------------------------ 
|          0           |          10          |          15          |         100          |          98          |
------------------------------------------------------------------------------------------------------------------
|          0           |          12          |          12          |         100          |          98          |
------------------------------------------------------------------------------------------------------------------
|          0           |          17          |          4           |         100          |         100          |
------------------------------------------------------------------------------------------------------------------
[Workload-gen] ----- Workload Generator Statistics -----
[Workload-gen] Total number of requests: 100
[Workload-gen] Total number of requests completed successfully: 100
[Workload-gen] Total number of failed requests: 0
[Workload-gen] Total number of correct predictions : 100
[Workload-gen] Total number of wrong predictions: 0
[Workload-gen] Total response time: 96.1222038269043 (seconds)
[Workload-gen] -----------------------------------

|          0           |          0           |          0           |         100          |         100          |
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |         100          |         100          |
------------------------------------------------------------------------------------------------------------------
|          0           |          0           |          0           |         100          |         100          |
------------------------------------------------------------------------------------------------------------------
[Test-Case-3-log] Waiting for 5sec for the resources to scale in ...
[AS-log] Time to scale in to 0 instances: 0.24 seconds.Points:[10/10]
[Test-Case-3-log] Stop event set. Waiting for autoscaling thread to finish.
|          0           |          0           |          0           |         100          |         100          |
------------------------------------------------------------------------------------------------------------------
[Test-Case-3-log] 100/100 entries in S3 bucket:1225754101-in-bucket.Points:[5.0/5]
[Test-Case-3-log] 100/100 entries in S3 bucket:1225754101-out-bucket.Points:[5.0/5]
[Test-Case-3-log] 100/100 correct predictions.Points:[10.0/10]
[Test-Case-3-log] Test average Latency: 0.961222038269043 sec. `avg latency<1.2s`.Points:[40/40]
[Test-Case-3-log] ---------------------------------------------------------
[AS-log] EC2 instances scale out as expected.Points:[15/15]
[AS-log] EC2 instances scale back to 0 as expected.Points:[5/5]
[AS-log] SQS messages in 1225754101-req-queue increased from 0 and reduced back to 0. [5/5]
[AS-log] SQS messages in 1225754101-resp-queue increased from 0 and reduced back to 0. [5/5]
[AS-log] S3 bucket:1225754101-in-bucket objects increased from 0 to 100.
[S3-log] Bucket:1225754101-in-bucket is now EMPTY !!
[AS-log] S3 bucket:1225754101-out-bucket objects increased from 0 to 100.
[S3-log] Bucket:1225754101-out-bucket is now EMPTY !!
[AS-log] ---------------------------------------------------------
Total Grade Points: 100.0
Removed extracted folder: extracted
Total time taken to grade for Doe John ASUID: 1225754101: 115.00062108039856 seconds
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Grading complete for Project-1. Check the Project-1-grades.csv file.

```
