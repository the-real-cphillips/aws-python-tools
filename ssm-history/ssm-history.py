#!/usr/bin/env python

import boto3
import time
import sys


def main():

    count = 0
    results = 20 if len(sys.argv) < 2 else sys.argv[1]

    tic = time.perf_counter()
    client = boto3.client('ssm')
    resource = boto3.resource('ec2')

    # Default pulls last 50 session
    sessions = client.describe_sessions(State='History', MaxResults=int(results))['Sessions']
    
    for session in sessions:
        count += 1
        instance = resource.Instance(id=session['Target'])
        name_tag = [ tags for tags in instance.tags if tags['Key'] == 'Name' ][0]['Value']
        print(f"Session Id: {session['SessionId']}\nTarget Instance: {name_tag}\nStarted: {session['StartDate']}\nTerminated:{session['EndDate']}\n")
    toc = time.perf_counter()
    print(f'[I] Elapsed Time: {toc-tic:0.2f}\n[I] Retrieved: {count} Entries')


if '__main__' in __name__:
    main()
