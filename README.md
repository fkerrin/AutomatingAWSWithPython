# AutomatingAWSWithPython
Following course on AWS automation using Python
I started this course on 3rd September 2018

4th September 2018 - set up AWS session user, set up Python environment with pipenv and created a folder for the first project - Puplishing Websiite to S3

5th September 2018 - added folder with basic Python script, using @click decorators to give CLI functionality to list S3 buckets and objects

5th September 2018 - added to script to set up S3 bucket, copy index.html and set up permissions and web hosting

6th September 2018 - added to script to sync files from local repository to S3 bucket

7th September 2018 - refactored code to separate out functions into a module as class methods

8-9th September 2018 - removed hardcoding of profile and url and stopped re-uploading of content already on S3

10-11th September 2018 - setup Route53 domain to point at S3 bucket - needs troubleshooting...

12-13th September 2018 - setup SSL certificate and CloudFront distribution - needs troubleshooting...

14-18th September 2018 - completed troubleshooting and created packaging

20th September 2018 - rough script for setting up an EC2 instance and giving restricted SSH access and public HTML access

21st September 2018 - rough script for auto-scaing events

23rd September 2018 - lambda function for Slack notifications on auto-scaling events in AWS

27th September 2018 - lmbda functions to send jobs to Rekognition and store results in DynamoDB for videos uploaded to S3