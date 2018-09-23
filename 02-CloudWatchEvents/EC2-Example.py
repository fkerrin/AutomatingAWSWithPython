"""This is just a dump of script commands from ipython to set up an EC2 instance"""
import boto3
import os, stat

"""To set up an EC2 instance, we need the following:
-   Key Pair
-   AMI - will look for an Amazon standard free tier AMI
-   Instance Type (e.g. t2.micrro as this is free tier
-   Security Group - a default will be created with EC2 but will have no permissions"""

if __name__ == '__main__':

    AWSSession = boto3.Session(profile_name = 'PythonUser')

    EC2 = AWSSession.resource('ec2')

    KeyPair = EC2.create_key_pair(KeyName = 'AutomateAWS')  # Create a Key Pair on AWS for our instance
    KeyPath = 'AutomateAWS.pem'  # What we will save the private key as locally

    KeyPair.key_material  # This gives the private part of the key pair

    with open(KeyPath, 'w') as KeyFile:
        KeyFile.write(KeyPair.key_material)  # Save the private key locally

    """SSH terminal may reject a key that has open permissions so we need to
    limit file permissions for the key to red/write access for local user only"""
    os.chmod(KeyPath, stat.S_IRUSR | stat.S_IWUSR)

    len(list(EC2.images.filter(Owners = ['amazon'])))  # This will show how many Amazon AMI images are avilable (over 5,000)

    # Go to the console and find an AMI that you want in your region (i.e. same region as AWSSession
    Image = EC2.Image('ami-047bb4163c506cd98')

    ImageName = Image.name  # This will return 'amzn-ami-hvm-2018.03.0.20180811-x86_64-gp2' for eu-west-1 (None elsewhere)

    Filters = [{'Name' : 'name', 'Values' : [ImageName]}]  # Set up a filter and search for the Image ID
    """Really need to hardcode the Image Name 'amzn-ami-hvm-2018.03.0.20180811-x86_64-gp2' and then find the ID with this filter"""
    ImageList = list(EC2.images.filter(Owners = ['amazon'], Filters = Filters))
    MyImage = ImageList[0]  # Should only get one result from this filter

    # Want the instance to be a simple website
    InstanceBootstrap = """
	    #!/bin/bash
        mkdir /var/www
        mkdir /var/www/html
        cd /var/www/html/
        echo '<html><head>Quick and Dirty Website...</head></html>' > index.html
        yum update -y
        yum install -y httpd
        service httpd start
        chkconfig httpd on"""
 
    MySecurityGroup = EC2.create_security_group(Description = 'WEB and SSH Access', GroupName = 'AWSAutomation')
    # Now want to add SSH access (restricted to my IP) and HTTP access (public) and add the instance to this SG
    # Note my public IP will change so check and insert actual IP before running this
    MySecurityGroup.authorize_ingress(CidrIp = '51.37.220.103/32', FromPort = 22, ToPort = 22, IpProtocol= 'tcp')
    MySecurityGroup.authorize_ingress(CidrIp = '0.0.0.0/0', FromPort = 80, IpProtocol = 'tcp', ToPort = 80)
    SGID = MySecurityGroup.group_id
	
    Instances = EC2.create_instances(ImageId = MyImage.id, MinCount=1, MaxCount=1, InstanceType = 't2.micro',
        KeyName=KeyPair.key_name, UserData = InstanceBootstrap, SecurityGroupIds = [SGID])

    MyInstance = Instances[0]  # Can create multiple EC2 but we only created one
    MyInstance.wait_until_running()  # Ensure the instance has started up - otherwise won't be able to query
	
    MyInstance.reload()  # Refresh the instance parameters - otherwise will not return data
    InstanceDNSName = MyInstance.public_dns_name
    InstanceIP = MyInstance.public_ip_address
    # Can use either of the above to SSH into the instance - ec2-user@InstanceDNSName or e2-user@InstanceIP

    # Print out the access details
    print('Public IP is:  {},  Public DNS is:  {}'.format(InstanceIP, InstanceDNSName))
    

"""Some ways to improve this script:
-   Check if key pair and security group exist and, if not, create them
-   Include auto-scaling as part of this script with min=max=1 to give resilience - multi-AZ
-   Add a load balancer
-   Make the website more generic - pull the content from S3 as part of bootstrap
"""
