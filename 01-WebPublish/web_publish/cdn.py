# -*- coding: utf-8 -*-

"""Classes for CDN (Amazon CloudFront) distribution."""


from uuid import uuid4


class CDNHandler:

    def __init__(self, Session):
        """Manage CDN distributions."""

        self.CDNClient = Session.client('cloudfront')

    
    def FindDistribution(self, DomainName):
        """Find an existing CloudFront Distibution for the domain."""

        Paginator = self.CDNClient.get_paginator('list_distributions')

        for Page in Paginator.paginate():
            for Item in Page['DistributionList']['Items']:
                if Item['Aliases']['Quantity']  == 0: continue  # No domains in this distribution
                for Alias in Item['Aliases']['Items']:  # Could be several aliases
                    if Alias == DomainName:
                        return Item  # Returns the dict for the distribution

        return None  # Didn't find a distribution for the domain


    def CreateDistribution(self, DomainName, CertARN):
        """Create a CloudFront distibution for the domain and certificate."""

        OriginID = 'S3-' + DomainName
        Dist = self.CDNClient.create_distribution(DistributionConfig = {
            'CallerReference' : str(uuid4()),
            'Aliases' :{
                'Quantity' : 1,  # Only creaating one alias
                'Items' : [DomainName]
            },
            'DefaultRootObject' : 'index.html',
            'Comment' : 'CloudFront distribution for fkerrin.com',
			'Enabled' : True,
            'Origins' : {
                'Quantity' : 1,
                'Items' : [{
                    'Id' : OriginID,
                    'DomainName' : '{}.s3.amazonaws.com'.format(DomainName),
                    'S3OriginConfig' : {
                        'OriginAccessIdentity' : ''
                    }
                }]
            },
            'DefaultCacheBehavior' : {
                'TargetOriginId' : OriginID,
                'ViewerProtocolPolicy' : 'redirect-to-https',  # If the user types http
                'TrustedSigners' : {
                    'Quantity' : 0,
                    'Enabled' : False
                },
                'ForwardedValues' : {
                    'Cookies' : {'Forward' : 'all'},
                    'Headers' : {'Quantity' : 0},
                    'QueryString' : False,
                    'QueryStringCacheKeys' : {'Quantity' : 0}
                },
                'DefaultTTL' : 86400,  # Time to live - 24h - for data to stey on cache
                'MinTTL' : 3600,  # Minimum time to live - 1h
            },
            'ViewerCertificate' : {
                'ACMCertificateArn' : CertARN,  # Passed this into the function call
                'SSLSupportMethod' : 'sni-only',  # Server Name Indication
                'MinimumProtocolVersion' : 'TLSv1.1_2016'
            }
        })
        """The CloudFront create_distribution() method has a huge number of options and
        only a small number of them are used here. For explanation of the parameters
        used here and the remaining options see the boto3 documentation."""

        return Dist['Distribution']


    def AwaitDistributionDeployment(self, Distribution):
        """Check if CloudFront distrubution has been deployed."""

        Waiter = self.CDNClient.get_waiter('distribution_deployed')
		
        Waiter.wait(Id = Distribution['Id'], WaiterConfig = 
            {'Delay' : 30, 'MaxAttempts' : 100})

        return
