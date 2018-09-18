# -*- coding: utf-8 -*-

""" Domains: Classes for Route 53 Domains on AWS """

from uuid import uuid4

class DomainHandler:
    """Manage Route 53 Domains."""


    def __init__(self, Session):
        """Create a Domain Handler object'"""
        
        self.Route53Client = Session.client('route53')


    def FindHostedZone(self, DomainName):
        """Find Hosted Zone in my account'"""

        Paginator = self.Route53Client.get_paginator('list_hosted_zones')

        for Page in Paginator.paginate():
            for Zone in Page['HostedZones']:
                # AWS puts a dot on the end of the zone name so ignore last character
                if DomainName.endswith(Zone['Name'][:-1]):
                    return Zone
                
        return None  # If you don't find the zone or paginator pages empty


    def CreateHostedZone(self, DomainName):
        """Create Hosted Zone in my account'"""

        # Domain Name is of the format subdomain.blablabla.fkerrin.com
        # Hosted Zone is fkerrin.com
        ZoneName = '.'.join(DomainName.split('.')[-2:]) + '.'
        """split('.') splits a string separated by dots into a list of substrings.
        '.'.join() does the opposite - creates a single string from a list of strings
        separated by dots. Route53 then requires a dot at the end."""

        return self.Route53Client.create_hosted_zone(
            Name = ZoneName,
            CallerReference = str(uuid4())  # Needs to be a unique string - uuid generates unique codes
            )['HostedZone']


    def CreateS3DomainRecord(self, Zone, DomainName, Endpoint):
        """Create A-Record for our bucket (same as DomainName) in our Route 53 hosted zone."""

        """The bucket name will be the same as the DomainName and the Endpoint will be calculated
        from the bucket region using the named tuple in utils.py and passed to this function."""
		
        return self.Route53Client.change_resource_record_sets(
            HostedZoneId = Zone['Id'],
			ChangeBatch = {
			    'Comment' : 'Creating Record Set to point at S3 bucket',
                'Changes' : [{  # Can be a list but here just doing one
                        'Action' : 'UPSERT',  # Update if exists or Insert if not
                        'ResourceRecordSet' : {
                            'Name' : DomainName,
							'Type' : 'A',  # Creating an A-Record
                            'AliasTarget' : {
                                'HostedZoneId' : Endpoint.HostedZoneID,
								'DNSName' : Endpoint.WebsiteEndpoint,
								'EvaluateTargetHealth' : False
                                }
                        }
                }]
            })  # If all went well should return the A-Record


    def CreateCloudFrontDomainRecord(self, Zone, DomainName, CDNDomainName):
        """Create A-Record for our bucket (same as DomainName) in our Route 53 hosted zone."""

        """The bucket name will be the same as the DomainName and the Endpoint will be calculated
        from the bucket region using the named tuple in utils.py and passed to this function."""
		
        return self.Route53Client.change_resource_record_sets(
            HostedZoneId = Zone['Id'],
			ChangeBatch = {
			    'Comment' : 'Creating Record Set to point at S3 bucket',
                'Changes' : [{  # Can be a list but here just doing one
                        'Action' : 'UPSERT',  # Update if exists or Insert if not
                        'ResourceRecordSet' : {
                            'Name' : DomainName,
							'Type' : 'A',  # Creating an A-Record
                            'AliasTarget' : {
                                'HostedZoneId' : 'Z2FDTNDATAQYW2',  # Same for any ClouFront Dist (see docs)
								'DNSName' : CDNDomainName,
								'EvaluateTargetHealth' : False
                                }
                        }
                }]
            })  # If all went well should return the A-Record

