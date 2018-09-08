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

from s3_bucket import BucketHandler

# Use guess_type to determine the content type being uploaded to S3
from mimetypes import guess_type
# Use pathlib to allow extraction of files and subdirectories to uploa to S3
from pathlib import Path, PurePosixPath
import boto3  # AWS API
from botocore.exceptions import ClientError  # Catch errors raised through API
import click  # Command line functionality through function decorators


@click.group()
def CLI():
    """Publish website to S3"""  # Docstring is the command description (--help option)
    pass


@CLI.command('ListBuckets')  # This string is the command to use with the script
def ListBuckets():
    """Lists all S3 Buckets in Account"""  # Docstring shows in the Command description
    for Bucket in BucketHandler(AWSSession).AllBuckets():
        print(Bucket)
    return


@CLI.command('ListBucketObjects')
@click.argument('bucket')
def ListBucketObjects(bucket):
    """Lists objects in S3 buckets"""
    for Object in BucketHandler(AWSSession).AllObjects(bucket):
        print(Object)
    return


@CLI.command('SetUpBucket')
@click.argument('bucket')  # Bucket name must be specifieed by a command line argument
def SetUpBucket(bucket):
    """Set up S3 bucket to host wehsite"""

    # Create the new bucket from the name provided
    NewBucket = BucketHandler(AWSSession).CreateBucket(bucket, AWSSession)

	# Now we need to create a bucket policy for web hosting permissions (copy from AWS documents on S3 web hosting)
    BucketHandler(AWSSession).SetBucketPolicy(NewBucket)

    # Set up web hosting on bucket and get the static website URL
    URL = BucketHandler(AWSSession).SetBucketWebHosting(NewBucket, AWSSession)
    print('The website URL is:  ', URL)
    
    return


@CLI.command('SyncWebFiles')
@click.argument('path_name', type = click.Path(exists = True))  # Click checks validity of input path name
@click.argument('bucket_name')  # S3 bucket to upload the files to
def SyncWebfilesToS3(path_name, bucket_name):
    """Sync contents of PATH_NAME to BUCKET_NAME"""
# Click will prompt if path_name is incorrect but prints it out in CAPS so want the message to match

    WebRoot = Path(path_name).expanduser().resolve()
    """This expands full path of the root for the web files and
    handles the case where the user puts ~/ rather than /Users/xxx/"""

    BucketHandler(AWSSession).CopyContentsToS3(WebRoot, bucket_name)

    return


if __name__ == '__main__':

    # Create session with AWS
    AWSSession = boto3.Session(profile_name = 'PythonUser')

    CLI()
    """This delegates control of the functions	to the CLI command group
	click will manage the flow. Note: If this module is imported (not __main__ ),
	the CLI command will be ignored and the functions are called normally"""
