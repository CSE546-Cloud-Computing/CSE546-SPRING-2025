# Autograder for Project 2 Part 1

Make sure that you use the provided autograder and follow the instructions below to test your project submission. Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.

- Download the zip file you submitted from Canvas. 
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - `cd CSE546-SPRING-2025/`
  - `git checkout project-2-part-1`
- Create a directory `submissions` in the CSE546-SPRING-2025 directory and move your zip file to the submissions directory.

## Prepare to run the autograder
- Install Python: `sudo apt install python3`
- Populate the `class_roster.csv`
  - If you are a student; replace the given template only with your details.
  - If you are a grader; use the class roster for the entire class
 
## Run the autograder
- To run the autograder: ```python3 autograder.py --num_requests 100 --img_folder="<dataset folder path>" --pred_file="<output classification csv file path>"```
- The autograder will look for submissions for each entry present in the class_roster.csv
- For each submission the autograder will
  - The autograder extracts the credentials.txt from the submission and parses the entries.
  - Use the Grader IAM credentials to test the project as per the grading rubrics and allocate grade points.
  - The autograder has a workload generator component to generate requests to your face-detection Lambda function.

## Sample Output

```
+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
- 1) Extract the credentials from the credentials.txt
- 2) Execute the test cases as per the Grading Rubrics
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
Project Path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-1/grader
Grade Project: Project-1
Class Roster: class_roster.csv
Zip folder path: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-1/grader/submissions
Grading script: /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-1/grader/grade_project2_p1.py
Test Image folder path: ../../datasets/frames
Classification results file: ../../datasets/FaceRecognitionResults.csv
Autograder Results: Project-1-grades.csv
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ Grading for Doe John ASUID: 1225754101 +++++++++++++++++++++
Extracted /home/local/ASUAD/kjha9/git/GTA-CSE546-SPRING-2025/Project-2/part-1/grader/submissions/Project2-1225754101.zip to extracted
File: extracted/credentials/credentials.txt has values ('XXXXXXXXXXX, 'XXXXXXXXXXX, ''XXXXXXXXXXX', ''XXXXXXXXXXX')
Credentials parsing complete.
-----------------------------------------------------------------
IAM ACCESS KEY ID: XXXXXXXXXXX
IAM SECRET ACCESS KEY: 'XXXXXXXXXXX
-----------------------------------------------------------------
Following policies are attached with IAM user:cse546-AutoGrader: ['IAMReadOnlyAccess', 'AmazonSQSFullAccess', 'AWSLambda_ReadOnlyAccess', ‘AWSLambdaSQSQueueExecutionRole’]
[IAM-log] AmazonSQSFullAccess policy attached with grading IAM
[IAM-log] AWSLambda_ReadOnlyAccess policy attached with grading IAM
[Cloudwatch-log] CAUTION !! You do not have a Cloudwatch alarm set. Kindly refer to the Project-0 document and learn how to set a billing alarm
-------------- CSE546 Cloud Computing Grading Console -----------
IAM ACCESS KEY ID: XXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXX
Face detection Lambda Function URL: XXXXXXXXXXX
SQS Response Queue URL:XXXXXXXXXXX
-----------------------------------------------------------------
----------------- Executing Test-Case:1 ----------------
[Lambda-log] The function: face_detection exists
[Lambda-log] The function: face-recognition-part-1 exists.
[Lambda-log] Points deducted:0
[Lambda-log] ---------------------------------------------------------
[Lambda-Trigger-log] SQS Trigger Found with Lambda func:face-recognition-part-1: arn:aws:sqs:us-east-1:XXXXXXXXXXX:1225754101-req-queue-fifo.fifo
[Lambda-Trigger-log] Points deducted:0
[Lambda-Trigger-log] ---------------------------------------------------------
[SQS-log] The expectation is that both the Request and Response SQS should exist and be EMPTY
[SQS-log] - WARN: This will purge any messages available in the SQS
[SQS-log] ---------------------------------------------------------
[SQS-log] SQS Request Queue:1225754101-req-queue has 0 pending messages.
[SQS-log] SQS Response Queue:1225754101-resp-queue has 0 pending messages.
[SQS-log] Points deducted:0
----------------- Executing Test-Case:2 ----------------
Starting workload generator... 
Workload complete! Dumping statistics...
[Workload-gen] ----- Workload Generator Statistics -----
[Workload-gen] Total number of requests: 100
[Workload-gen] Total number of requests completed successfully: 100
[Workload-gen] Total number of failed requests: 0
[Workload-gen] Total number of correct predictions : 100
[Workload-gen] Total number of wrong predictions: 0
[Workload-gen] Total test duration: 178.29808926582336 (seconds)
[Workload-gen] ------------------------------------------

[Test-Case-3-log] 100/100 completed successfully.Points:[20.0/20]
[Test-Case-3-log] 100/100 correct predictions.Points:[20.0/20]
[Test-Case-3-log] Test Average Latency: 1.7829808926582337 sec. `avg latency<3s`.Points:[60/60]
[Test-Case-3-log] ---------------------------------------------------------
Total Grade Points: 100.0
Removed extracted folder: extracted
Total time taken to grade for Doe John ASUID: 1225754101: 183.52135705947876 seconds
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Grading complete for Project-2. Check the Project-2-grades.csv file.
```
