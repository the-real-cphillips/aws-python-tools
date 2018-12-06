#!/usr/bin/env python
import boto3
import sys

region = sys.argv[1]
cidr_block = sys.argv[2]
sg_list = []


def connection(region):
    return boto3.client('ec2', region_name=region)


def find_cidr_in_sg(connection, cidr):
    marker = None
    while True:
        paginator = connection.get_paginator('describe_security_groups')
        response_iterator = paginator.paginate(
            PaginationConfig={
                'PageSize': 10,
                'StartingToken': marker
            }
        )
        for page in response_iterator:
            for sg in page['SecurityGroups']:
                for ip_perms in sg['IpPermissions']:
                    for ip_range in ip_perms['IpRanges']:
                        if cidr in ip_range['CidrIp']:
                            sg_list.append(sg['GroupName'])
        try:
            marker = page['Marker']
        except KeyError:
            break

def main():
    count = 0
    find_cidr_in_sg(connection(region), cidr_block)

    for sg in sorted(set(sg_list)):
        print(sg)
        count += 1
    print('Total Count: ' + '' + str(count))


if __name__ == '__main__':
    main()
