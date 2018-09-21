import boto3

if __name__ == '__main__':

    AWSSession = boto3.Session(profile_name = 'PythonUser')
    ASClient = AWSSession.client('autoscaling')

    ASClient.describe_auto_scaling_groups()
    ASClient.describe_policies()

    ASGroups = ASClient.describe_auto_scaling_groups()
    # This returns a dict in which there is a list of groups under the 'AutoScalingGroups' key
    ASGNames = []
    for Item in ASGroups['AutoScalingGroups']:
        ASGNames.append(Item['AutoScalingGroupName'])  # Creates a list of the autoscaling group names

    # The following code similarly creates a list of autoscaling policies
    ASPolicies = []
    for Item in ASClient.describe_policies()['ScalingPolicies']:
        ASPolicies.append(Item['PolicyName'])

    # Now can scale up and scale down using script commands - policies returned were ScaleUp and ScaleDown
    ASClient.execute_policy(AutoScalingGroupName = 'TestingPython', PolicyName = 'ScaleUp')
    ASClient.execute_policy(AutoScalingGroupName = 'TestingPython', PolicyName = 'ScaleDown')
