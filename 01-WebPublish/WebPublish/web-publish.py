# This is part of the AcloudGuru course "Automating AWS with Python
# This project is to synchrronise a website to S3 for diistribution over CloudFront

import boto3
import click

MySession = boto3.Session(profile_name = 'PythonUser')

S3 = MySession.resource('s3')

@click.group()
def CLI():
    'Publish website to S3'  # This docstring is the command description (using the --help option)
    pass

@CLI.command('ListBuckets')
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


if __name__ == '__main__':
    CLI()  # Delegates control of the functions to teh CLI command group - click will manage the flow
