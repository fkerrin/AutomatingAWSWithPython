import os  # Needed to retrieve environment variables
import requests  # Have to pip install requests /path (serverless directory) to include with the package

def PostToSlack(event, context):
    """Receive triggers from auto-scaling events and post message to Slack."""

    slack_url = os.environ['SLACK_WEBHOOK']
    Message = '{} detected on Auto-Scaling Group {} at {}'.format(event['detail-type'], event['detail']['AutoScalingGroupName'], event['time']) 
    Data = {'text' : Message}
    requests.post(slack_url, json = Data)

    return
