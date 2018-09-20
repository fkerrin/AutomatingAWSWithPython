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
from domains import DomainHandler
from certificates import CertificateHandler
from cdn import CDNHandler
import utils
import boto3  # AWS API
import click  # Command line functionality through function decorators


@click.group()
@click.option('--profile', default = None,
    help = 'Supply a valid AWS profile name for account')
def CLI(profile):
    """Publish website to S3"""  # Docstring is the command description (--help option)
    
    global AWSSession, bucket_handler, domain_handler, cert_handler, cdn_handler
    """Need global to ensure we modify the global versions and not create new
    variables that would not be accessible to our other functons."""

    session_config = {}  # dict onject to be passed to boto3 below
    if profile:
        session_config['profile_name'] = profile

    # Create session with AWS
    AWSSession = boto3.Session(**session_config)
    # Create an instance of the BucketHandler class
    bucket_handler = BucketHandler(AWSSession)
    domain_handler = DomainHandler(AWSSession)
    cert_handler = CertificateHandler(AWSSession)
    cdn_handler = CDNHandler(AWSSession)


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


@CLI.command('SetUpDomain')
@click.argument('domain_name')  # User supplies domain name to setup
def SetupRoute53Domain(domain_name):
    """Configure DOMAIN_NAME to point to bucket of the same name."""

    bucket_name = domain_name  # One constraint is that the bucket name matches the domain name

    # Check if the requested zone exists, if not, create it
    Zone = domain_handler.FindHostedZone(domain_name) \
	    or domain_handler.CreateHostedZone(domain_name)

    Endpoint = utils.GetEndpoint(bucket_handler.GetBucketRegion(bucket_name))

    domain_handler.CreateS3DomainRecord(Zone, domain_name, Endpoint)

    print("Domain Configured:  http://{}".format(domain_name))

    return


@CLI.command('SetUpCDN')
@click.argument('domain_name')
def SetUPCDN(domain_name):
    """Set up CDN distribution for the site."""

    # Check if we have already have a CDN distribution for the domain
    CDNDist = cdn_handler.FindDistribution(domain_name)
    # If none exists we create one
    if not CDNDist:
        Cert = cert_handler.GetCertificateForDomain(domain_name)
        if not Cert:
            print("Cannot proceed - SSL certificate is required for CloudFront Distribution.")
            return

        CDNDist = cdn_handler.CreateDistribution(domain_name, Cert)
        print("Awaiting deployment of CDN distribution....")
        cdn_handler.AwaitDistributionDeployment(CDNDist)

    # Check if the hosted zone exists, if not, create it
    Zone = domain_handler.FindHostedZone(domain_name) \
	    or domain_handler.CreateHostedZone(domain_name)

    # Finally, need to create the CloudFront domain reccord in Route 53
    domain_handler.CreateCloudFrontDomainRecord(Zone, domain_name, CDNDist['DomainName'])

    print("Domain Configured:  https://{}".format(domain_name))


if __name__ == '__main__':

    """ Create globaal variables for AWS session and bucket resource to be
   set up and utilised by all functions in the script"""
    AWSSession = None
    bucket_handler = None
    domain_handler = None
    cert_handler = None
    cdn_handler = None

    CLI()
    """This delegates control of the functions	to the CLI command group
	click will manage the flow. Note: If this module is imported (not __main__ ),
	the CLI command will be ignored and the functions are called normally"""
