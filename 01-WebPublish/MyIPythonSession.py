# coding: utf-8
import boto3

MySession = boto3.Session(profile_name = 'PythonUser')

S3 = MySession.resource('s3')
    
for Bucket in S3.buckets.all():
    print(Bucket)
