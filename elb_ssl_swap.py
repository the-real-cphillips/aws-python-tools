#!/usr/bin/env python
import boto3
import sys

# I plan on converting this to argparse at some point

elb_name = sys.argv[1]
port = int(sys.argv[2])
ssl_id = sys.argv[3]
region = sys.argv[4]
account_number = sys.argv[5]

client = boto3.client('elb', region_name=region)

def swap_ssl(elb_name, port, account_number, ssl_id):
    """ Swap SSL Certs on ELBs, specific usage for ACM Certs """
    response = client.set_load_balancer_listener_ssl_certificate(
            LoadBalancerName=elb_name,
            LoadBalancerPort=port,
            SSLCertificateId="arn:aws:acm:%s:%s:certificate/%s" % (region, account_number, ssl_id)
            )
    return response

def main():
    print swap_ssl(elb_name, port, account_number, ssl_id)

if __name__ == '__main__':
    main()
