# -*- coding: utf-8 -*-

""" web-publish: Deploy websites with AWS

web-publish automates the process of deploying static websites to AWS
- Configure AWS S3 buckets
  - Create them
  - Set them uoo for statc web hosting
  - Deploy local files to them
- Configure DNS with AWS Route 53
- Configure a Content Delivery Network and SSL with AWS CloudFront
"""

# Use guess_type to determine the content type being uploaded to S3
from mimetypes import guess_type
# Use pathlib to allow extraction of files and subdirectories to uploa to S3
from pathlib import Path, PurePosixPath
import boto3  # AWS API
from botocore.exceptions import ClientError  # Catch errors raised through API
import click  # Command line functionality through function decorators


# Create session with AWS
MySession = boto3.Session(profile_name = 'PythonUser')

S3 = MySession.resource('s3')  # Create S3 resource object


@click.group()
def CLI():
    """Publish website to S3"""  # Docstring is the command description (--help option)
    pass


@CLI.command('ListBuckets')  # This string is the command to use with the script
def list_buckets():
    """Lists all S3 Buckets in Account"""  # Docstring shows in the Command description
    for Bucket in S3.buckets.all():
        print(Bucket)


@CLI.command('ListBucketObjects')
@click.argument('bucket')
def ListBucketObjects(bucket):
    """Lists objects in S3 buckets"""
    for Object in S3.Bucket(bucket).objects.all():
        print(Object)


@CLI.command('SetUpBucket')
@click.argument('bucket')  # Bucket name must be specifieed by a command line argument
def SetUpBucket(bucket):
    """Set up S3 bucket to host wehsite"""
# Create the new bucket from the name provided
    try:
        NewBucket = S3.create_bucket(Bucket = bucket, CreateBucketConfiguration = {'LocationConstraint' : MySession.region_name})
# Region needs to be specified explicitly, at least outside us-east-1
# If the bucket exists there will be an error - if I own it it's OK, else supplied bucket name cannot be used
    except ClientError as Err:
        if Err.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            NewBucket=S3.Bucket(bucket)  # Set the bucket as the already existing and owned one
        else:
            raise Err  # Any other error just raise it and exit program

# Now we need to create a bucket policy for web hosting permissions (copy from AWS documents on S3 web hosting)
# The """ is for text over multiple lines
# The { must come straight after as otherwise BucketPolicy will start with \n and not be accepted
    BucketPolicy = """{
      "Version":"2012-10-17",
      "Statement":[{
        "Sid":"PublicReadGetObject",
        "Effect":"Allow",
        "Principal": "*",
        "Action":["s3:GetObject"],
        "Resource":["arn:aws:s3:::%s/*"]
      }]
    }""" %NewBucket.name
# Template string %s gets replaced by what is immediately after the string - i.e. NewBucket.name

# Now need to apply this to the bucket - done in a roundabout way with boto3:
# Need to create a policy object from the bucket Policy() method and put that to the bucket
    NewBucketPolicy = NewBucket.Policy()
    NewBucketPolicy.put(Policy = BucketPolicy)

# Now need to set web hosting on the bucket - again roundabout
# Need to create a Website object and put it on the bucket
    Website = NewBucket.Website()
    Website.put(WebsiteConfiguration = {
        'ErrorDocument' : {'Key' : 'error.html'}, 'IndexDocument' : {'Suffix' : 'index.html'}
        })
# 'Suffix' is the default file that is presented if the browser request does not include a specific html page

# Now need to create the URL name from the bucket and region - AWS has a standard format
    URL = 'http://' + NewBucket.name + '.s3-website-' + MySession.region_name + '.amazonaws.com'
    print(URL)
    
    return


@CLI.command('SyncWebFiles')
@click.argument('path_name', type = click.Path(exists = True))  # Click checks validity of input path name
@click.argument('bucket_name')  # S3 bucket to upload the files to
def sync_webfiles_to_s3(path_name, bucket_name):
    """Sync contents of PATH_NAME to BUCKET_NAME"""
# Click will prompt if path_name is incorrect but prints it out in CAPS so want the message to match

    MyPath = Path(path_name)
    WebRoot = MyPath.expanduser().resolve()
# This expands full path and handles the case where the user puts ~/ rather than /Users/xxx/
    WebBucket = S3.Bucket(bucket_name)

# Path supplied should be root of the website files (where index.html should be)
# Traverse through all these subdirectories and copy subdirectory structure and files to S3
    def RecurseDirectory(start_path):
        for Object in start_path.iterdir():
            if Object.is_dir():
                RecurseDirectory(Object)  # Continue to iterate through subdirectories
            if Object.is_file():
                LocalPath = str(Object)
# S3 won't be able to deal with Windows backslashes so use PurePosixPath() to convert to Unix format
                Key = str(PurePosixPath(Object.relative_to(WebRoot)))
# Use mimetypes function guess_type() to guess file type or use default if it fails to guess a type
                content_type = guess_type(Key)[0] or 'text/plain'
                WebBucket.upload_file(LocalPath, Key, ExtraArgs = {'ContentType' : content_type})
# Key is what will be sent to S3 - Subdirs/File
        return

    RecurseDirectory(WebRoot)

    return


if __name__ == '__main__':
    CLI()  # Delegates control of the functions to teh CLI command group - click will manage the flow
