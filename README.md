# Autograder for Project 1 Part 1

Make sure that you use the provided autograder and follow the instructions below to test your project submission. Failure to do so may cause you to lose all the project points and there will be absolutely no second chance.

- Download the zip file you submitted from Canvas. 
- Download the autograder from GitHub: `https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - In order to clone the GitHub repository follow the below steps:
  - `git clone https://github.com/CSE546-Cloud-Computing/CSE546-SPRING-2025.git`
  - `cd CSE546-SPRING-2025/`
  - `git checkout project-1-part-1`
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
  - Validate if the zip file adheres to the submission guidelines as mentioned in the project document.
    - If Yes; proceed to next step
    - If No; allocate 0 grade points and proceed to the next submission
  - The autograder extracts the credentials.txt from the submission and parses the entries.
  - Use the Grader IAM credentials to test the project as per the grading rubrics and allocate grade points.
  - The autograder will dump stdout and stderr in a log file named `autograder.log`
      
## Sample Output

```
+++++++++++++++++++++++++++++++ CSE546 Autograder  +++++++++++++++++++++++++++++++
- 1) The script will first look up for the zip file following the naming conventions as per project document
- 2) The script will then do a sanity check on the zip file to make sure all the expected files are present
- 3) Extract the credentials from the credentials.txt
- 4) Execute the test cases as per the Grading Rubrics
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++++++++++++ Autograder Configurations ++++++++++++++++++++++++++++
Project Path: /Users/kritshekhar/git/GTA-CSE546-SPRING-2025/Project-1/part-1/grader
Grade Project: Project-1
Class Roster: class_roster.csv
Zip folder path: /Users/kritshekhar/git/GTA-CSE546-SPRING-2025/Project-1/part-1/grader/submissions
Test zip contents script: /Users/kritshekhar/git/GTA-CSE546-SPRING-2025/Project-1/part-1/grader/test_zip_c
ontents.sh
Grading script: /Users/kritshekhar/git/GTA-CSE546-SPRING-2025/Project-1/part-1/grader/grade_project0.py
Test Image folder path: ../web-tier/upload_images/
Classification results file: ../../Classification Results on Face Dataset (1000 images).csv
Autograder Results: Project-1-grades.csv
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
++++++++++++++++++ Grading for Doe John ASUID: 1225754101 +++++++++++++++++++++
Extracted /home/local/ASUAD/kjha9/git/cse546-github-test/CSE546-SPRING-2025/submissions/Project1-1225754101.zip to extracted
File: extracted/credentials/credentials.txt has values ('XXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'XX.XXX.XX.XX')
Unzip submission and check folders/files: PASS
Credentials parsing complete.
-----------------------------------------------------------------
IAM ACESS KEY ID: XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
-----------------------------------------------------------------
Following policies are attached with IAM user:cse546-AutoGrader: ['IAMReadOnlyAccess', 'AmazonEC2ReadOnlyAccess', 'AmazonS3FullAccess', 'SecurityAudit']
[IAM-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[IAM-log] AmazonS3FullAccess policy attached with grading IAM
[Cloudwatch-log] CAUTION !! You do not have a Cloudwatch alarm set. Kindly refer to the Project-0 document and learn how to set a billing alarm
-------------- CSE546 Cloud Computing Grading Console -----------
IAM ACESS KEY ID: XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
IAM SECRET ACCESS KEY: XXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Web-Instance IP Address: XX.XXX.XX.XX
-----------------------------------------------------------------
----------------- Executing Test-Case:2 ----------------
[EC2-log] AmazonEC2ReadOnlyAccess policy attached with grading IAM
[EC2-log] EC2-state Pass. web-tier instance found. With state: running.Points deducted: 0
[S3-log] AmazonS3FullAccess policy attached with grading IAM
[S3-log] - WARN: If there are objects in the S3 buckets; they will be deleted
[S3-log] ---------------------------------------------------------
[S3-log] S3 Bucket:1225754101-in-bucket has 0 object(s). Points deducted:0
[DB-log] SimpleDB Domain: 1225754101-simpleDB exist
[DB-log] SimpleDB Domain: 1225754101-simpleDB exist with 1000 items. Points deducted:0
----------------- Executing Test-Case:3 ----------------
[Workload-gen] Attempt-1 100/100 requests successful.
[Workload-gen] All requests have been processed or retried.
[Workload-gen] ----- Workload Generator Statistics -----
[Workload-gen] Total number of requests: 100
[Workload-gen] Total number of requests completed successfully: 100
[Workload-gen] Total number of failed requests: 0
[Workload-gen] Total number of correct predictions : 100
[Workload-gen] Total number of wrong predictions: 0
[Workload-gen] Total Test Duration: 0.7521615028381348 (seconds)
[Workload-gen] -----------------------------------

[S3-log] Bucket:1225754101-in-bucket is now EMPTY !!
[Test-Case-3-log] 100/100 entries in S3 bucket:1225754101-in-bucket.Points:[20.0/20]
[Test-Case-3-log] 100/100 completed successfully.Points:[20.0/20]
[Test-Case-3-log] 100/100 correct predictions.Points:[20.0/20]
[Test-Case-3-log] Test Latency: 0.7521615028381348 sec. `latency<=3`.Points:[40/40]
Total Grade Points: 100.0
Removed extracted folder: extracted
Execution Time for Doe John ASUID: 1225754101: 4.614058494567871 seconds
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Grading complete for Project-1. Check the Project-1-grades.csv file.
  ```
