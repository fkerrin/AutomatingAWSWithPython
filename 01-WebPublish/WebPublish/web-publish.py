# This is part of the AcloudGuru course "Automating AWS with Python
# This project is to synchrronise a website to S3 for diistribution over CloudFront

import boto3
import click
from botocore.exceptions import ClientError  # To catch errors raised through the API

MySession = boto3.Session(profile_name = 'PythonUser')

S3 = MySession.resource('s3')

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

@CLI.command('SetupBucket')
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

if __name__ == '__main__':
    CLI()  # Delegates control of the functions to teh CLI command group - click will manage the flow
