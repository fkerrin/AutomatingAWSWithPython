# This is part of the AcloudGuru course "Automating AWS with Python
# This project is to synchrronise a website to S3 for diistribution over CloudFront

import boto3  # AWS API
import click  # Command line functionality through function decorators
from mimetypes import guess_type  # To determine the content type being uploaded to S3
from botocore.exceptions import ClientError  # To catch errors raised through the API
from pathlib import Path, PurePosixPath  # To allow extraction of files and subdirectories to uploa to S3

MySession = boto3.Session(profile_name = 'PythonUser')  # Create session with AWS

S3 = MySession.resource('s3')  # Create S3 resource object

@click.group()
def CLI():
    'Publish website to S3'  # This docstring is the command description (using the --help option)
    pass

@CLI.command('ListBuckets')  # This string is the command to use with the script
def list_buckets():
    "Lists all S3 Buckets in Account"  # This docstring shows in the Command description
    for Bucket in S3.buckets.all():
        print(Bucket)

@CLI.command('ListBucketObjects')
@click.argument('bucket')
def ListBucketObjects(bucket):
    'Lists objects in S3 buckets'
    for Object in S3.Bucket(bucket).objects.all():
	    print(Object)

@CLI.command('SetUpBucket')
@click.argument('bucket')  # Bucket name must be specifieed by a command line argument
def SetUpBucket(bucket):
    'Set up S3 bucket to host wehsite'
# Create the new bucket from the name provided
    try:
        NewBucket = S3.create_bucket(Bucket = bucket, CreateBucketConfiguration = {'LocationConstraint' : MySession.region_name})
# Region needs to be specified explicitly, at least outside us-east-1
# If the bucket exists there will be an error - if I own it it's OK but if not, the supplied bucket name cannot be used
    except ClientError as Err:
	    if Err.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
		    NewBucket = S3.Bucket(bucket)  # Set the bucket as the already existing and owned one
	    else:
		    raise Err  # Any other error just raise it and exit program

# Upload the index.html file - note directory separators are / rather than Windows standard \ - I could get click() to take ths as a command line argument
    NewBucket.upload_file('/AWS/Python/AutomateAWS/AutomatingAWSWithPython/01-WebPublish/WebPublish/index.html', 'index.html', ExtraArgs={'ContentType' : 'text/html'})
# This copies the specified local file to a file called index.html of text/html format to the specified bucket

# Now we need to create a bucket policy for web hosting permissions (copied from AWS documents on S3 web hosting
# The """ is for text over multiple lines - the { comes straight after as otherwise BucketPolicy will start with /n and not be accepted
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
# Now need to apply this to the bucket - done in a roundabout way with boto3 by creating a policy object from the bucket Policy() method and putting that to the bucket
    NewBucketPolicy = NewBucket.Policy()
    NewBucketPolicy.put(Policy = BucketPolicy)

# Now need to set web hosting on the bucket - again roundabout - create a Website object and put it on the bucket
    Website = NewBucket.Website()
    Website.put(WebsiteConfiguration = {'ErrorDocument' : {'Key' : 'error.html'}, 'IndexDocument' : {'Suffix' : 'index.html'}})
# 'Suffix' is the default file that is presented if the browser request does not include a specific html page

# Now need to create the URL name from the bucket and region - AWS has a standard format
    URL = 'http://' + NewBucket.name + '.s3-website-' + MySession.region_name + '.amazonaws.com'
    print(URL)
	
    return

@CLI.command('SyncWebFiles')
@click.argument('path_name', type = click.Path(exists = True))  # Click will check validity of the input path name
@click.argument('bucket_name')  # S3 bucket to upload the files to
def sync_webfiles_to_s3(path_name, bucket_name):
    "Sync contents of PATH_NAME to BUCKET_NAME"  # Click will prompt if path_name is incorrect but prints it out in CAPS

    MyPath = Path(path_name)
    WebRoot = MyPath.expanduser().resolve()  # Expands full path and handles the case where the user puts ~/ rather than /Users/xxx/
    WebBucket = S3.Bucket(bucket_name)

# The path supplid should be the root of the website files (index.html should be in the root) go through all these and copy to S3	
    def RecurseDirectory(start_path):
        for Object in start_path.iterdir():
            if Object.is_dir():
                RecurseDirectory(Object)  # Continue to iterate through subdirectories
            if Object.is_file():
                LocalPath = str(Object)
                Key = str(PurePosixPath(Object.relative_to(WebRoot)))  # S3 won't be able to deal with Windows backslashes
                content_type = guess_type(Key)[0] or 'text/plain'  # Default assigned if mimetypes cannot guess type
                WebBucket.upload_file(LocalPath, Key, ExtraArgs = {'ContentType' : content_type})  # Key is what will be sent to S3 - Subdirs/File
        return
    
    RecurseDirectory(WebRoot)

    return
	

if __name__ == '__main__':
    CLI()  # Delegates control of the functions to teh CLI command group - click will manage the flow
