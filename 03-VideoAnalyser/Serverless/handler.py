import boto3
import urllib
import os
import json

def start_label_detection(Bucket, Key):
    """This function kicks off the video analysis job to Rekognition."""

    ImageClient = boto3.client('rekognition')  # Note - don't need session in Lambda - it uses roles automatically created by Serverless

    RekognitionMessage = ImageClient.start_label_detection(
        Video = {'S3Object' : 
            {'Bucket' : Bucket, 'Name' : Key}
        },
        MinConfidence = float(os.environ['MINIMUM_CONFIDENCE_LEVEL']),
        NotificationChannel = {'SNSTopicArn' : os.environ['REKOGNITION_TOPIC_ARN'],
            'RoleArn' : os.environ['REKOGNITION_ROLE_ARN']})

    RekognitionJob = RekognitionMessage['JobId']

    return


def get_video_labels(RekognitionJobID):
    """Build the labels for the video analysis through multiple calls to Rekognition."""

    ImageClient = boto3.client('rekognition')

    AnalysisResult = ImageClient.get_label_detection(JobId = RekognitionJobID)
    Labels = AnalysisResult['Labels']
	
    while 'NextToken' in AnalysisResult.keys():  # If there are more results to get there will be a NextToken parameter
        next_token = AnalysisResult['NextToken']
        AnalysisResult = ImageClient.get_label_detection(JobId = RekognitionJobID, NextToken = next_token)
        Labels.extend(AnalysisResult['Labels'])  # extend() extends the list, append() would just add a single item
	
    return Labels


def add_new_label(UniqueLabelList, Label):
    """Add a new item to the list of labels for a video."""

    NewLabel = {}
    NewLabel['LabelName'] = Label['Label']['Name']
    NewLabel['Confidence'] = Label['Label']['Confidence']
    NewLabel['TimeStamps'] = [Label['Timestamp']]
    NewLabel['Count'] = 1
	
    UniqueLabelList.append(NewLabel)
	
    return NewLabel
	
	
def update_label(UniqueLabel, Label):
    """Update an item in the list of labels for a video."""

    UniqueLabel['Confidence'] = ((UniqueLabel['Confidence'] * UniqueLabel['Count']) + Label['Label']['Confidence'])/(UniqueLabel['Count'] + 1)
    UniqueLabel['TimeStamps'].append(Label['Timestamp'])
    UniqueLabel['Count'] += 1
	
    return
	
	
def FixFloats(Data):
    """Recursively go through a data structure and convert any floats to string."""

    if isinstance(Data, dict):
        return { k: FixFloats(v) for k, v in Data.items() }

    if isinstance(Data, list):
        return [ FixFloats(v) for v in Data ]

    if isinstance(Data, float):  # Only floats being changed here
        return str(Data)

    return Data
	
	
def update_database(JobData, Labels):
    """Take the Rekognition data for a video and add to a DynamoDB."""

    DB = boto3.resource('dynamodb')
    DBTable = DB.Table(os.environ['DB_TABLE_NAME'])
	
    DBData = {}
    DBData['VideoID'] = JobData['JobId']
    DBData['VideoName'] = JobData['Video']['S3ObjectName']
    DBData['S3Bucket'] = JobData['Video']['S3Bucket']
    DBData['Labels'] = []
	
	# Now want to create a list of unique labels, number of occurrences, time of occurrences and average confidence
    for Label in Labels:
        if len(DBData['Labels']) == 0:  # Populate the first item
            add_new_label(DBData['Labels'], Label)
        else:
            FoundMatch = False
            for UniqueLabel in DBData['Labels']:
                if Label['Label']['Name'] == UniqueLabel['LabelName']:
                    update_label(UniqueLabel, Label)
                    FoundMatch = True
                    break
            # If we haven't found a match, need to add another unique label
            if not FoundMatch: add_new_label(DBData['Labels'], Label)

    # Now put this into the database. DynamoDB doesn't support Python float format so fix this
    DBData = FixFloats(DBData)
    DBTable.put_item(Item = DBData)

    return


def start_video_analysis(event, context):  # This is the Lambda handler to kick off Rekognition job
    """Receive a trigger for new S3 object and send it for video analysis."""

    for Record in event['Records']:  # There may have been more than one file uploaded
        Bucket = Record['s3']['bucket']['name']
        NewFileUploaded = urllib.parse.unquote_plus(Record['s3']['object']['key'])
        # Remove the "+" signs of url encoding and return original whitespaces to the filename
        start_label_detection(Bucket, NewFileUploaded)
    
    return


def label_detection(event, context):  # This is the Lambda handler for label retrieval
    """Receive SNS trigger to say Rekognition job complete - get results and add to DynamoDB."""

    for Record in event['Records']:
        RekognitionJob = json.loads(Record['Sns']['Message'])
        # Message is a json encapsulated as a string - loads() decodes to json
        if RekognitionJob['Status'] != 'SUCCEEDED':
            print('Rekognition Job {}'.format(RekognitionJob['Status']))
            return

        RekognitionJobID = RekognitionJob['JobId']

        # get_label_detection() returns max 1000 labels so need a handler to get all if over 1000
        VideoLabels = get_video_labels(RekognitionJobID)
        update_database(RekognitionJob, VideoLabels)

    return


"""Some possible ways to improve this script:
-  Further decoupling - all labels are retrieved in one call to label_detection()
   and this function handles the paging between calls to Rekognition get_video_labels()
   could use separate lambda function for each call - this would avoid hitting the 5min
   limit on lambda for a very long video.
-  Deal with floats better than converting to string
-  Write a function to retrieve thee data and present it to the user
