"""This is just a dump of script commands from ipython to set up an EC2 instance"""
import boto3

"""To set up an EC2 instance, we need the following:
-   Key Pair
-   AMI - will look for an Amazon standard free tier AMI
-   Instance Type (e.g. t2.micrro as this is free tier
-   Security Group - a default will be created with EC2 but will have no permissions"""

AWSSession = boto3.Session(profile_name = 'PythonUser')

EC2 = AWSSession.resource('ec2')

KeyPair = EC2.create_key_pair(KeyName = 'AutomateAWS')  # Create a Key Pair on AWS for our instance
KeyPath = 'AutomateAWS.pem'  # What we will save the private key as locally

KeyPair.key_material  # This gives the private part of the key pair

with open(KeyPath, 'w') as KeyFile:
    KeyFile.write(KeyPair.key_material)  # Save the private key locally

"""SSH terminal may reject a key that has open permissions so we need to
limit file permissions for the key to red/write access for local user only"""
import os, stat
os.chmod(KeyPath, stat.S_IRUSR | stat.S_IWUSR)

len(list(EC2.images.filter(Owners = ['amazon'])))  # This will show how many Amazon AMI images are avilable (over 5,000)

# Go to the console and find an AMI that you want in your region (i.e. same region as AWSSession
Image = EC2.Image('ami-047bb4163c506cd98')

ImageName = Image.name  # This will return 'amzn-ami-hvm-2018.03.0.20180811-x86_64-gp2' for eu-west-1 (None elsewhere)

Filters = [{'Name' : 'name', 'Values' : [ImageName]}]  # Set up a filter and search for the Image ID
"""Really need to hardcode the Image Name 'amzn-ami-hvm-2018.03.0.20180811-x86_64-gp2' and then find the ID with this filter"""
ImageList = list(EC2.images.filter(Owners = ['amazon'], Filters = Filters))
MyImage = ImageList[0]  # Should only get one result from this filter

Instances = EC2.create_instances(ImageId = MyImage.id, MinCount=1, MaxCount=1, InstanceType='t2.micro', KeyName=KeyPair.key_name)

MyInstance = Instances[0]  # Can create multiple EC2 but we only created one

SGID = MyInstance.security_groups[0]['GroupId']
SGID
SG = MyInstance.security_groups[0]  # Lists the security groups (should only be one at this stage - default created with instancce)
# Default security group has no access - want to add SSH access from a single IP - my public IP
SG.authorize_ingress(CidrIp='109.77.44.68/32', FromPort=22, ToPort=22, IpProtocol= 'tcp')

InstanceDNSName = MyInstance.public_dns_name
InstanceIP = MyInstance.public_ip_address
# Can use either of the above to SSH into the instance - ec2-user@InstanceDNSName or e2-user@InstanceIP

# Also want to add HTTP access from any public IP
SG.authorize_ingress(CidrIp='0.0.0.0/0', FromPort=80, IpProtocol= 'tcp', ToPort=80)

"""Now SSH into the instance and set up as a webbserver:
sudo yum update -y
sudo install httpd -y
sudo service httpd start

Then put an index,html in /var/www/html/ and access from browser using public IP or DNS name"""

