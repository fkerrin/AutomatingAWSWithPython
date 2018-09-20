# -*- coding: utf-8 -*-

"""Classes for ACM (Amazon Certificate Manager) certificates."""

class CertificateHandler:

    def __init__(self, Session):
        """Manage ACM certificaes."""

        self.ACMClient = Session.client('acm', region_name = 'us-east-1')
        """ Need to force the region to us-east-1, as this is the only region
	    that supports SSL certificates on CloudFront"""
	
    
    def CertMatches(self, CertARN, DomainName):
        """Verify if any domains on the given certificate match required domain."""

        CertDetails = self.ACMClient.describe_certificate(CertificateArn = CertARN)
        AltNames = CertDetails['Certificate']['SubjectAlternativeNames']

        """AltNames is a list of names that are assigned to the certificate. We want
        to test if any of these either matches the domain name supplied exactly or
        if fits to a wildcard range - e.g. *.example.com."""
        for Name in AltNames:
            if Name == DomainName:
                return True
            if Name[0] == '*' and DomainName.endswith(Name[1:]):
                return True

        return False  # Didn't find a match


    def GetCertificateForDomain(self, DomainName):
        """Find a certificatee issued to the specified domain."""

        Paginator = self.ACMClient.get_paginator('list_certificates')
		
        for Page in Paginator.paginate(CertificateStatuses = ['ISSUED']):  # Only check issued certificates
            for Cert in Page['CertificateSummaryList']:  # Just look at the certificates
                if self.CertMatches(Cert['CertificateArn'], DomainName):
                    return Cert['CertificateArn']

        return None  # If we can't get a certificate for this domain








