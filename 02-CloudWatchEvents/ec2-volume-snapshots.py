# This will list EC2 instances filtered on tags, list associated volumes and take snapshots of thsse volumes
# Also lists all s3 buckets

import boto3  # API inerface to AWS
import botocore  # To handle exceptions in AWS access
import click  # Facilitates CLI (command line interfaces)

# Need to create a session using a pre-configured profile based on an AMI user with programmatic access
session = boto3.Session(profile_name = "PythonUser")
ec2 = session.resource("ec2")
s3 = session.resource("s3")

#  @click.command()  # Decorator function - hand off control of the function and ccmmand line argument handling to click()
def list_instances(instances):
    for i in instances:
        print(i,
              "  Status: ", i.state["Name"],
              "  Public IP: ", i.public_ip_address,
              "  Private IP: ", i.private_ip_address,
              "  Availability Zone: ", i.placement["AvailabilityZone"])

        for v in i.volumes.all():  # Each instance in the iteration can have one or more volumes attached
            print("   Volume attached to ", i.id, ":  ", v.id,
                  "State: ", v.state,
                  "Size: ", str(v.size), "GiB",  # size attribute is an integer - convert to string
                  "Encryption: ", v.encrypted and "Encrypted" or "Not Encrypted")  # encrypted attribute is boolean - want it to display sensibly
            for s in v.snapshots.all():
                print("      Snapshot for this volume: ", s.id,
                      " Completion: ", s.progress,
                      " Created: ", s.start_time.strftime("%c"))  # start_time attribute not helpfil - srftime() formats according to predefined formats
    return

def list_buckets():
    for i in s3.buckets.all():
        print("Bucket Name:  ", i.name)
    return

def create_snapshots(instances):  # Creates snapshot for all volumes attached to instances iin the collection "instances"
# For each instance, stop, create instance, restart and move onto next instance
    for i in instances:

        try:  # Don't want to start the snapshot until instance is stopped
            i.stop()
            print("Stopping {0}...".format(i.id))
            i.wait_until_stopped()
        except botocore.exceptions.ClientError as err:
            print(" Could not stop {0}. ".format(i.id) + str(err))  # Tried to stop a pending instance
            continue

        for v in i.volumes.all():  # Wanto snapshot all volumes for the instancee
            if has_pending_snapshot(v):  # Snapshot already in progress - no need to create snapshot
                print(" Skipping {0}, snapshot already in progress".format(v.id))
                continue

            print(" Creating snapshot of {0}".format(v.id))
            v.create_snapshot(Description = "Created by Python")  # Add description to know who did snapshot

        try:  # Don't do next instance until this instance restarts - don't want all instances to go down together
            i.start()
            print("Starting {0}...".format(i.id))
            i.wait_until_running()
        except botocore.exceptions.ClientError as err:
            print(" Could not start {0}. ".format(i.id) + str(err))  # Tried to start a stopping instance
        continue
# Note - not sure if the above exceptions are working - I couldn't get these to fail by starting and stopping from console during execution

    return

def has_pending_snapshot(volume):  # Test for snapsots in progress so we can ignore them and go to next
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == "pending"  # Boolean - True if there are snapshots and the latest one is still pending


if __name__ == "__main__":
    filters = [{"Name" : "tag:Project", "Values" : ["Python"]}]
    instances = ec2.instances.filter(Filters = filters)  # Interested only in instances with the Tag specified in the filter

    list_instances(instances)

    print("Listted out all EC2, now list out all S3")
    list_buckets()

    print("Now we want to create snapshot of all instances related to project ", filters[0]["Values"])
    create_snapshots(instances)
