# -*- coding: utf-8 -*-

""" s3_bucket: Classes for accessing and managing S3 resources on AWS """

import utils  # Helper data and functions
# Use guess_type to determine the content type being uploaded to S3
from mimetypes import guess_type
# Use pathlib to allow extraction of files and subdirectories to uploa to S3
from pathlib import Path, PurePosixPath
from hashlib import md5
from functools import reduce
import boto3  # AWS API
from botocore.exceptions import ClientError  # Catch errors raised through API

class BucketHandler:
    """Handle all S3 bucket operations."""
    
    CHUNK_SIZE = 8388608  # Chunk size threshold for S3 multipart uploads

    def __init__(self, Session):
        """Create S3 bucket resource."""
        self.S3 = Session.resource('s3')
        self.TransferConfig = boto3.s3.transfer.TransferConfig(
            multipart_chunksize = self.CHUNK_SIZE, multipart_threshold = self.CHUNK_SIZE)
		# This sets the multipart chunk size for our transfers - need to use this in S3 uploads

        self.ETagCache = {}  # Store the ETags of files already on S3


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
		
        Bucket.Policy().put(Policy = BucketPolicy)
        return

		
    def GetBucketRegion(self, BucketName):
        """Return the region of a bucket."""
		
        bucket_location = self.S3.meta.client.get_bucket_location(Bucket = BucketName)

        return bucket_location['LocationConstraint'] or 'us-east-1'
        # Note that us-east-1 returns None for the LocaionConstraint so need to deal with this edge case


    def GetBucketURL(self, Bucket):
        """Get the URL given the bucket name."""

        # First get the region for the bucket
        BucketRegion = self.GetBucketRegion(Bucket.name)

        # Verify we have this region in our list and return the corresponding endpoint
        if utils.ValidateRegion(BucketRegion):
            return 'http://{}.{}'.format(Bucket.name, utils.GetEndpoint(BucketRegion).WebsiteEndpoint)
        else: return None

		
    def SetBucketWebHosting(self, Bucket, Session):
        """Set the bucket to host web content."""

        # Do by creating a Website object and applying it (put) to the bucket
        Bucket.Website().put(WebsiteConfiguration = {
            'ErrorDocument' : {'Key' : 'error.html'},
            'IndexDocument' : {'Suffix' : 'index.html'}
            })
        """'Suffix' is the default file that is presented if the browser request
		does not include a specific html page"""

        # Create URL name from the bucket and region - AWS has a standard format
        URL = self.GetBucketURL(Bucket)
        return URL


    def GetS3ObjectETags(self, Bucket):
        """Caching ETags for S3 objects to compaaree with local objectt ETags
        and avoid unnecessary re-uploading."""
        
        # Create a paginator object and page through it to find S3 contents and add to ETagCache
        Paginator = self.S3.meta.client.get_paginator('list_objects_v2')
		
        for Page in Paginator.paginate(Bucket = Bucket.name):
            if 'Contents' in Page:
                for Object in Page['Contents']:
                    self.ETagCache[Object['Key']] = Object['ETag']
                    """Here the bucket objects are found under the 'Contents' section of nested
                    dict objects returned by the paginaor. We want to match the object name (which
                    is called ['Key'] in the ['Contents'] sub-dictionary) with the 'ETag'. To add to
                    a dict, the syntax is MyDict['Key'] = 'Value' - in our case the Key is
                    Object['Key'] which is why we end up with double [] above"""
            else: pass  # If there are no objects, there is nothing to add to the ETag cache
        return


    @staticmethod
    def HashData(Data):
        """Generate md5 hash for data."""
        hash = md5()
        hash.update(Data)
        return hash


    def GenerateLocalETag(self, FilePath):
        """Generate ETag for local files to compare with S3 ETag."""
        HashCodes = []
        
        with open(FilePath, 'rb') as File:
            while True:  # Will loop until we break out
                Data = File.read(self.CHUNK_SIZE)
                if not Data: break  # Either empty file or EOF
                
                HashCodes.append(self.HashData(Data))
        
        """Three different possible outcomes:
        - The file is empty - just return
        - The file is less than 8MB - will only have one hash - return it
        - The file is multipart, has multiple hashes - hash them and return result"""
        if not HashCodes: return
        elif len(HashCodes) == 1:
            return '"{}"'.format(HashCodes[0].hexdigest())
        else:
            Hash = self.HashData(reduce(lambda x, y: x + y, (h.digest() for h in HashCodes)))
            # This takes the digest for each multipart hash, adds them and hashes the result
            return '"{}-{}"'.format(Hash.hexdigest(), len(HashCodes))
        """Note: To compare with S3 ETag it needs to be in double quotes - hence the '"{}"'.format()
        Also, the multipart hash includes the number of parts followed by the hash of ETags"""


    def CopyContentsToS3(self, PathName, BucketName):
        """Copy contents of given path to the specified bucket."""
        
        WebRoot = Path(PathName).expanduser().resolve()
        """This creates a Patth object from the supplied path name. It also expands full path of the root
        for the web files and handles the case where the user puts ~/ rather than /Users/xxx/"""

        Bucket = self.S3.Bucket(BucketName)

        # Firstly get the ETags for the files already in S3 and store in ETagCache{}
        self.GetS3ObjectETags(Bucket)
		
    # Traverse through subdirectories and copy subdirectory structure and files to S3
        def RecurseDirectory(start_path):
            for Object in start_path.iterdir():
                if Object.is_dir():
                    RecurseDirectory(Object)  # Continue to iterate through subdirectories
                if Object.is_file():
                    LocalPath = str(Object)
                    ObjectToUpload = Object.relative_to(WebRoot)
                    """If the object to upload is not on S3 then go ahead and upload
                    otherwise, calculate the local Etag and compare with S3 Etag."""
                    Key = str(PurePosixPath(ObjectToUpload))
                    if Key in self.ETagCache:
                        LocalHash = self.GenerateLocalETag(Object)
                        if LocalHash == self.ETagCache[Key]: pass  # Same object is in S3 already
                        else:  # Upload the object
                            content_type = guess_type(Key)[0] or 'text/plain'
                            Bucket.upload_file(LocalPath, Key, 
                                ExtraArgs = {'ContentType' : content_type},
                                Config = self.TransferConfig)
                            print("Uploaded file: {}".format(Key))
                    else:  # Object not on S3 so upload it
                        content_type = guess_type(Key)[0] or 'text/plain'
                        Bucket.upload_file(LocalPath, Key,
                            ExtraArgs = {'ContentType' : content_type},
                            Config = self.TransferConfig)
                        print("Uploaded file: {}".format(Key))
                        """Key is what will be sent to S3 - Subdirs/File. Use mimetypes function guess_type()
			            to guess file type or use default if it fails to guess a type. PurePosixPath is used
                        to convert any Windows backslashes to forward slashes that S3 can deal with"""

        RecurseDirectory(WebRoot)  # Start the recursion from the root of where the files are stored
        return

