# -*- coding: utf-8 -*-

"""Helper utilities for our functions."""

from collections import namedtuple

EndPoint = namedtuple('Endpoint', ['RegionName', 'WebsiteEndpoint', 'HostedZoneID'])

EndPointForRegion = {
    'us-east-2' : EndPoint('US East (Ohio)', 's3-website.us-east-2.amazonaws.com', 'Z2O1EMRO9K5GLX'),
    'us-east-1' : EndPoint('US East (N. Virginia)', 's3-website-us-east-1.amazonaws.com', 'Z3AQBSTGFYJSTF'),
    'us-west-1' : EndPoint('US West (N. California)', 's3-website-us-west-1.amazonaws.com', 'Z2F56UZL2M1ACD'),
    'us-west-2' : EndPoint('US West (Oregon)', 's3-website-us-west-2.amazonaws.com', 'Z3BJ6K6RIION7M'),
    'ca-central-1' : EndPoint('Canada (Central)', 's3-website.ca-central-1.amazonaws.com', 'Z1QDHH18159H29'),
    'ap-south-1' : EndPoint('Asia Pacific (Mumbai)', 's3-website.ap-south-1.amazonaws.com', 'Z11RGJOFQNVJUP'),
    'ap-northeast-2' : EndPoint('Asia Pacific (Seoul)', 's3-website.ap-northeast-2.amazonaws.com', 'Z3W03O7B5YMIYP'),
    'ap-northeast-3' : EndPoint('Asia Pacific (Osaka-Local)', 's3-website.ap-northeast-3.amazonaws.com', 'Z2YQB5RD63NC85'),
    'ap-southeast-1' : EndPoint('Asia Pacific (Singapore)', 's3-website-ap-southeast-1.amazonaws.com', 'Z3O0J2DXBE1FTB'),
    'ap-southeast-2' : EndPoint('Asia Pacific (Sydney)', 's3-website-ap-southeast-2.amazonaws.com', 'Z1WCIGYICN2BYD'),
    'ap-northeast-1' : EndPoint('Asia Pacific (Tokyo)', 's3-website-ap-northeast-1.amazonaws.com', 'Z2M4EHUR26P7ZW'),
    'cn-northwest-1' : EndPoint('China (Ningxia)', 's3-website.cn-northwest-1.amazonaws.com.cn', 'None'),
    'eu-central-1' : EndPoint('EU (Frankfurt)', 's3-website.eu-central-1.amazonaws.com', 'Z21DNDUVLTQW6Q'),
    'eu-west-1' : EndPoint('EU (Ireland)', 's3-website-eu-west-1.amazonaws.com', 'Z1BKCTXD74EZPE'),
    'eu-west-2' : EndPoint('EU (London)', 's3-website.eu-west-2.amazonaws.com', 'Z3GKZC51ZF0DB4'),
    'eu-west-3' : EndPoint('EU (Paris)', 's3-website.eu-west-3.amazonaws.com', 'Z3R1K369G5AVDG'),
    'sa-east-1' : EndPoint('South America (Sao Paulo)', 's3-website-sa-east-1.amazonaws.com', 'Z7KQH4QJS55SO')
    }

def ValidateRegion(region):
    """Confirm the supplied region exists in the list."""
    return region in EndPointForRegion  # For a dictionary, the keyword 'in' returns true if the key exists

def GetEndpoint(region):
    """For the region specified, get the appropriate endpoint from the list."""
    return EndPointForRegion[region].WebsiteEndpoint
