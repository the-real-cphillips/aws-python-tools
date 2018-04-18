#!/usr/bin/env python
import argparse
import boto3
import botocore
import sys
from datetime import timedelta
from datetime import datetime

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def from_file(filename):
    with open(filename) as bucket_file:
        bucket_list = bucket_file.readlines()
    bucket_list = [x.strip() for x in bucket_list]
    return bucket_list


def connection(service, profile, region_name='us-east-1'):
    session = boto3.Session(profile_name=profile)
    client = session.client(service, region_name=region_name)
    return client


def get_bucket_location(bucket_name):
    location = connection('s3', args.profile_name).get_bucket_location(Bucket=bucket_name)['LocationConstraint']
    if location is None:
        bucket_location = 'us-east-1'
    else:
        bucket_location = location
    return bucket_location


def get_metrics(region_name, NameSpace, MetricName, BucketName, Days, StorageType, Period=86400):
    start_time = datetime.utcnow() - timedelta(days=Days)
    end_time = datetime.utcnow()
    response = connection('cloudwatch', args.profile_name, region_name).get_metric_statistics(
        Namespace=NameSpace,
        MetricName=MetricName,
        StartTime=start_time,
        EndTime=end_time,
        Period=Period,
        Statistics=['Average'],
        Dimensions=[
            {'Name': 'BucketName', 'Value': BucketName},
            {u'Name': 'StorageType', u'Value': StorageType},
        ]
    )
    return response


def output_formatter(metric_response):
    for datapoint in metric_response['Datapoints']:
        if args.metric_name == 'BucketSizeBytes':
            return humansize(datapoint['Average'])
        else:
            return str(int(datapoint['Average']))


def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


def main():
    bucket_list = []
    if args.filename:
        bucket_list = from_file(args.filename)
    else:
        bucket_list.append(args.bucket_name)

    for bucket in bucket_list:
        try:
            region_name = get_bucket_location(bucket)
        except botocore.exceptions.ClientError as e:
            print "ERROR: %s: %s" % (bucket, e)
            return
        try:
            metric_response = get_metrics(region_name, 'AWS/S3', args.metric_name, bucket, args.days, args.storage_type)
            print "%s : %s" % (bucket, output_formatter(metric_response))
        except botocore.exceptions.EndpointConnectionError as e:
            print "ERROR: %s: %s" % (bucket, e)
            return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Find S3 Metrics from Cloudwatch",
                                     formatter_class=argparse.RawTextHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-b', '--bucket-name',
                       dest='bucket_name',
                       action='store',
                       help='Name of an S3 Bucket')
    group.add_argument('-f', '--filename',
                       dest='filename',
                       action='store',
                       help='Name of file containing bucket names one per line.')
    parser.add_argument('-d', '--days',
                        dest='days',
                        type=int,
                        default='2',
                        action='store',
                        help='Number of "Days ago" to pull datapoints from\nDefault: 2')
    parser.add_argument('-m', '--metric-name',
                        dest='metric_name',
                        default='BucketSizeBytes',
                        action='store',
                        help="Type of Metric to check for:\n"
                        "BucketSizeBytes | NumberOfObjects\n"
                        "Default: BucketSizeBytes")
    parser.add_argument('-s', '--storage-type',
                        dest='storage_type',
                        default='StandardStorage',
                        action='store',
                        help="Type of Storage to check for:\n"
                        "StandardStorage | StandardIAStorage | ReducedRedundancyStorage | AllStorageTypes\n"
                        "Default: StandardStorage")
    parser.add_argument('-p', '--profile-name',
                        dest='profile_name',
                        default='default',
                        action='store',
                        help="Use different profile in ~/.aws/credentials: default is named default")
    args = parser.parse_args()
    main()
