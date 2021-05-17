#!/usr/bin/env python
import argparse
import boto3
import time


def get_args():
    parser = argparse.ArgumentParser(
            description='Switch State of an Instance')
    parser.add_argument('-p', '--profile_name',
            action='store',
            dest='profile_name',
            default='default',
            help='AWS Profile Name')
    parser.add_argument('-r', '--region_name',
            action='store',
            dest='region_name',
            default='us-west-2',
            help='AWS Region Name')
    parser.add_argument('-i', '--instance-id',
            action='store',
            dest='instance_id',
            required=True,
            help='Instance Id')
    return parser.parse_args()


def connection(region_name='us-west-2', profile_name='default'):
    session = boto3.Session(
            profile_name=profile_name,
            region_name=region_name)
    client = session.client('ec2')
    resource = session.resource('ec2')
    return client, resource


def get_instance_state(resource, instance_id):
    instance = resource.Instance(id=instance_id)
    return instance.state['Name']


def stop(client, resource, instance_id):
    waiter = client.get_waiter('instance_stopped')
    instance = resource.Instance(id=instance_id)
    instance.stop()

    print(f'[I] Attempting to Stop {instance.id}')

    try:
        waiter.wait(InstanceIds=[instance.id])
        print(f'[√] {instance.id} Stopped')
        return True
    except botocore.exceptions.WaiterError as e:
        print(e.message)
        return False


def start(client, resource, instance_id):
    waiter = client.get_waiter('instance_running')
    instance = resource.Instance(id=instance_id)
    instance.start()

    print(f'[I] Attempting to Start {instance.id}')

    try:
        waiter.wait(InstanceIds=[instance.id])
        print(f'[√] {instance.id} Running')
        return True
    except botocore.exceptions.WaiterError as e:
        print(e.message)
        return False


def main():
    args = get_args()
    client, resource = connection(region_name=args.region_name, profile_name=args.profile_name)

    tic = time.perf_counter()
    print(f'[I] Determining State of {args.instance_id}')
    state = get_instance_state(resource, args.instance_id)

    if state == 'running':
        stop(client, resource, args.instance_id)
    else: 
        start(client, resource, args.instance_id)
    toc = time.perf_counter()
    print(f'Completed in {toc-tic:0.2f} seconds')


if '__main__' in __name__:
    main()
