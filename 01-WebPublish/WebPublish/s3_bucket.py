# -*- coding: utf-8 -*-

""" s3_bucket: Classes for accessing and managing S3 resources on AWS """

# Use guess_type to determine the content type being uploaded to S3
from mimetypes import guess_type
# Use pathlib to allow extraction of files and subdirectories to uploa to S3
from pathlib import Path, PurePosixPath
import boto3  # AWS API
from botocore.exceptions import ClientError  # Catch errors raised through API

class BucketHandler:
    """Handle all S3 bucket operations."""
    
    def __init__(self, session):
        """Create S3 bucket resource."""
        self.S3 = session.resource('s3')


    def AllBuckets(self):
        """Get an iterator for all S3 buckets."""
        return self.S3.buckets.all()


    def AllObjects(self, Bucket):
        """Get an iterator for all objects in bucket."""
        return self.S3.Bucket(Bucket).objects.all()


    def CreateBucket(self, BucketName, Session):
        """Create a new bucket, or keep existing."""
        try:
            NewBucket = self.S3.create_bucket(Bucket = BucketName,
                CreateBucketConfiguration = {'LocationConstraint' : Session.region_name})
                # Region needs to be specified explicitly, at least outside us-east-1
        except ClientError as Err:
            """If the bucket exists there will be an error. If I own it it's OK,
            otherwise supplied bucket name cannot be used"""
            if Err.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                NewBucket = self.S3.Bucket(BucketName)  # Set the bucket as my already existing one
            else:
                raise Err  # Any other error just raise it and exit program
        return NewBucket


    def SetBucketPolicy(self, Bucket):
        """Apply public read policy to bucket."""

        """The below policy was copied from AWS documentation on static S3 web hosting
		The { must come straight after as otherwise BucketPolicy will start with \n and
		not be accepted"""
		
        BucketPolicy = """{
          "Version":"2012-10-17",
          "Statement":[{
            "Sid":"PublicReadGetObject",
            "Effect":"Allow",
            "Principal": "*",
            "Action":["s3:GetObject"],
            "Resource":["arn:aws:s3:::%s/*"]
          }]
        }""" %Bucket.name
# Template string %s gets replaced by what is immediately after the string - i.e. NewBucket.name

        """Now need to apply this to the bucket - done in a roundabout way with boto3 by creating
		a policy object from the bucket Policy() method and applying that (put) to the bucket"""
		
        BucketPolicyObject = Bucket.Policy()
        BucketPolicyObject.put(Policy = BucketPolicy)
        return

		
    def SetBucketWebHosting(self, Bucket, Session):
        """Set the bucket to host web content."""

        # Do by creating a Website object and applying it (put) to the bucket
        Website = Bucket.Website()
        Website.put(WebsiteConfiguration = {
            'ErrorDocument' : {'Key' : 'error.html'},
            'IndexDocument' : {'Suffix' : 'index.html'}
            })
        """'Suffix' is the default file that is presented if the browser request
		does not include a specific html page"""

        # Create URL name from the bucket and region - AWS has a standard format
        URL = 'http://' + Bucket.name + '.s3-website-' + Session.region_name + '.amazonaws.com'
        
        return URL


    def CopyContentsToS3(self, FilePath, BucketName):
        """Copy contents of given path to the specified bucket."""
        
        Bucket = self.S3.Bucket(BucketName)

    # Traverse through subdirectories and copy subdirectory structure and files to S3
        def RecurseDirectory(start_path):
            for Object in start_path.iterdir():
                if Object.is_dir():
                    RecurseDirectory(Object)  # Continue to iterate through subdirectories
                if Object.is_file():
                    LocalPath = str(Object)
                    Key = str(PurePosixPath(Object.relative_to(FilePath)))
                    content_type = guess_type(Key)[0] or 'text/plain'
                    Bucket.upload_file(LocalPath, Key, ExtraArgs = {'ContentType' : content_type})
            """Key is what will be sent to S3 - Subdirs/File. Use mimetypes function guess_type()
			to guess file type or use default if it fails to guess a type. PurePosixPath is used
            convert any Windows backslashes to forward slashes that S3 can deal with"""

            return

        RecurseDirectory(FilePath)
        return

