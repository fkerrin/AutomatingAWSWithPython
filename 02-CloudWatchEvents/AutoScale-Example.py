import boto3

if __name__ == '__main__':

    AWSSession = boto3.Session(profile_name = 'PythonUser')
    ASClient = AWSSession.client('autoscaling')

    ASGroups = ASClient.describe_auto_scaling_groups()
    # This returns a dict in which there is a list of groups under the 'AutoScalingGroups' key
    ASGNames = []
    for Item in ASGroups['AutoScalingGroups']:
        ASGNames.append(Item['AutoScalingGroupName'])  # Creates a list of the autoscaling group names
    print('Auto-Scaling Groups found:  {}'.format(ASGNames))

    # The following code similarly creates a list of autoscaling policies
    ASPolicies = []
    for Item in ASClient.describe_policies()['ScalingPolicies']:
        ASPolicies.append(Item['PolicyName'])
    print('Auto-Scaling Policies found:  {}'.format(ASPolicies))

    # Now can scale up and scale down using script commands - policies returned were ScaleUp and ScaleDown
    ASClient.execute_policy(AutoScalingGroupName = ASGNames[0], PolicyName = 'ScaleUp')
#    ASClient.execute_policy(AutoScalingGroupName = ASGNames[0], PolicyName = 'ScaleDown')
