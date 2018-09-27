import boto3
from pathlib import Path

AWSSession = boto3.Session(profile_name = 'PythonUser')  # Need an S3 bucket for Rekognition to access media files
ImageClient = AWSSession.client('rekognition')
S3 = AWSSession.resource('s3')

VideoBucket = S3.create_bucket(Bucket = 'fkerrin-video-bucket', CreateBucketConfiguration = {'LocationConstraint' : AWSSession.region_name})

PathName = 'C:\AWS\VideosAndImages\Aerial Shot Of City.mp4'
FilePath = Path(PathName).expanduser().resolve()

VideoBucket.upload_file(str(FilePath), str(FilePath.name))
# FilePath is the local path, FilePath.name gives just the filename - this is the key that will be the S3 filename - just in the root of the bucket

Response = ImageClient.start_label_detection(Video = {'S3Object' : {'Bucket' : VideoBucket.name, 'Name' : str(FilePath.name)}})

print(Response)

RekognitionJob = Response['JobId']
print(RekognitionJob)
# The initial response of start_label_detection() gives the Job ID - the actual job continues in the background

AnalysisResult = ImageClient.get_label_detection(JobId = RekognitionJob)
# The result will be a long list of labels - create a list of the most relevant - use the percentage confidence value for relevance
AnalysisLabels = []
print(AnalysisResult['JobStatus'])
# Will need an if loop here - 3 conditions are 'IN_PROGRESS', 'SUCCEEDED', 'FAILED' - if in progress will nneed to put in a waiter, when succeeded do the below

for Item in AnalysisResult['Labels']:
    if Item['Label']['Confidence']  > 80.0:
        AnalysisLabels.append(Item['Label'])

print(len(AnalysisLabels))  # For a short clip (1m15), this yielded almost 300 labels - raise the bar a bit...

AnalysisLabels = []
for Item in AnalysisResult['Labels']:
    if Item['Label']['Confidence']  > 90.0:
        AnalysisLabels.append(Item['Label'])

print(len(AnalysisLabels))
for Item in AnalysisLabels:
    print(Item)
