#!/usr/bin/env python
import boto3
import sys
from datetime import timedelta
from datetime import datetime
from hurry.filesize import size,si

buckets = sys.argv[1]
bucket_list = []

def s3_connection():
    client = boto3.client('s3')
    return client

def get_bucket_location(bucket_name):
    location = s3_connection().get_bucket_location(Bucket=bucket_name)['LocationConstraint']
    if location is None:
        bucket_location = 'us-east-1'
    else:
        bucket_location = location
    return bucket_location

def cw_connection(region_name):
    client = boto3.client('cloudwatch', region_name=region_name)
    return client

def get_metrics(region_name, NameSpace, MetricName, BucketName,  Period=86400):
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()
    response = cw_connection(region_name).get_metric_statistics(
            Namespace=NameSpace,
            MetricName=MetricName,
            StartTime=start_time,
            EndTime=end_time,
            Period=Period,
            Statistics=['Average'],
            Dimensions=[
                {'Name':'BucketName','Value': BucketName},
                {u'Name': 'StorageType',u'Value': 'StandardStorage'}
            ]
    )
    return response

def output_formatter(metric_response):
    for datapoint in metric_response['Datapoints']:
        return size(datapoint['Average'], system=si)


def main():
    bucket_list = buckets.split(',')
    for bucket_name in bucket_list:
        region_name = get_bucket_location(bucket_name)
        metric_response = get_metrics(region_name, 'AWS/S3', 'BucketSizeBytes', bucket_name)
        print "%s Size: %s" % (bucket_name, output_formatter(metric_response))

if __name__ == '__main__':
    main()

