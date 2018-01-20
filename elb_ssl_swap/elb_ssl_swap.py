#!/usr/bin/env python
import argparse
import boto3
import sys
from termcolor import colored, cprint


parser = argparse.ArgumentParser(description="Swap ACM Certs on an ELB")

parser.add_argument('-r', '--region',
                    dest='region',
                    action='store',
                    default='us-west-2',
                    help="Specify region, default is us-west-2")
parser.add_argument('-p', '--port',
                    dest='port',
                    action='store',
                    default=443,
                    type=int,
                    help="Specify Listener port, default is 443")
parser.add_argument('-a', '--account_number',
                    dest='account_number',
                    action='store',
                    required=True,
                    help="AWS Account Number")
parser.add_argument('-c', '--cert_id',
                    dest='cert_id',
                    action='store',
                    required=True,
                    help="ACM Certificate ID")
parser.add_argument('-e', '--elb_name',
                    dest='elb_name',
                    action='store',
                    required=True,
                    help="AWS ELB Name")

args = parser.parse_args()

client = boto3.client('elb', region_name=args.region)

def swap_ssl(elb_name, port, account_number, cert_id, region):
    """ Swap SSL Certs on ELBs, specific usage for ACM Certs """
    try:
        response = client.set_load_balancer_listener_ssl_certificate(
            LoadBalancerName=elb_name,
            LoadBalancerPort=port,
            SSLCertificateId="arn:aws:acm:%s:%s:certificate/%s" % (region, account_number, cert_id)
            )
        return response
    except client.exceptions.AccessPointNotFoundException as error_message:
        return error_message
        

def parse_response(response):
    try:
        response = response['ResponseMetadata']['HTTPStatusCode']
    except TypeError:
        cprint("[x] Something went wrong, please check your values again", 'red')

    if type(response) is int:
        if response == 200:
            cprint("[O] Success! ELB: %s's SSL Cert was Updated" % (args.elb_name), 'green')


def main():
    response = swap_ssl(args.elb_name, args.port, args.account_number, args.cert_id, args.region)
    parse_response(response)


if __name__ == '__main__':
    main()
