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
import boto3  # AWS API
import click  # Command line functionality through function decorators


@click.group()
@click.option('--profile', default = None,
    help = 'Supply a valid AWS profile name for account')
def CLI(profile):
    """Publish website to S3"""  # Docstring is the command description (--help option)
    
    global AWSSession, bucket_handler
    """Need global to ensure we modify the global versions and not create new
    variables that would not be accessible to our other functons."""

    session_config = {}  # dict onject to be passed to boto3 below
    if profile:
        session_config['profile_name'] = profile

    # Create session with AWS
    AWSSession = boto3.Session(**session_config)
    # Create an instance of the BucketHandler class
    bucket_handler = BucketHandler(AWSSession)


@CLI.command('ListBuckets')  # This string is the command to use with the script
def ListBuckets():
    """Lists all S3 Buckets in Account"""  # Docstring shows in the Command description
    for Bucket in bucket_handler.AllBuckets():
        print(Bucket)
    return


@CLI.command('ListBucketObjects')
@click.argument('bucket')
def ListBucketObjects(bucket):
    """Lists objects in S3 buckets"""
    for Object in bucket_handler.AllObjects(bucket):
        print(Object)
    return


@CLI.command('SetUpBucket')
@click.argument('bucket')  # Bucket name must be specifieed by a command line argument
def SetUpBucket(bucket):
    """Set up S3 bucket to host wehsite"""

    # Create the new bucket from the name provided
    NewBucket = bucket_handler.CreateBucket(bucket, AWSSession)

	# Now we need to create a bucket policy for web hosting permissions (copy from AWS documents on S3 web hosting)
    bucket_handler.SetBucketPolicy(NewBucket)

    # Set up web hosting on bucket and get the static website URL
    URL = bucket_handler.SetBucketWebHosting(NewBucket, AWSSession)
    print('The website URL is:  ', URL)
    
    return


@CLI.command('SyncWebFiles')
@click.argument('path_name', type = click.Path(exists = True))  # Click checks validity of input path name
@click.argument('bucket_name')  # S3 bucket to upload the files to
def SyncWebfilesToS3(path_name, bucket_name):
    """Sync contents of PATH_NAME to BUCKET_NAME"""
    # Click will prompt if path_name is incorrect but prints it out in CAPS so want the message to match

    bucket_handler.CopyContentsToS3(path_name, bucket_name)

    return


if __name__ == '__main__':

    """ Create globaal variables for AWS session and bucket resource to be
   set up and utilised by all functions in the script"""
    AWSSession = None
    bucket_handler = None

    CLI()
    """This delegates control of the functions	to the CLI command group
	click will manage the flow. Note: If this module is imported (not __main__ ),
	the CLI command will be ignored and the functions are called normally"""
