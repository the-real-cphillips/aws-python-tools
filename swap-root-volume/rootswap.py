#!/usr/bin/env python
import argparse
import botocore
import boto3
import time
import sys


def get_args():
    parser = argparse.ArgumentParser(
            description="Switch Root Partition for Encrypted ones!",
            epilog="You switch the order of the lines around. How do you tell a joke badly?")
    parser.add_argument('-p', '--profile_name',
                        action='store',
                        dest='profile_name',
                        default='default',
                        help='AWS Profile Name')
    parser.add_argument('-r', '--region_name',
                        action='store',
                        dest='region_name',
                        default='us-west-2',
                        help='AWS Region')
    parser.add_argument('-i', '--instance-id',
                       action='store',
                       required=True,
                       dest='instance_id',
                       help='Instance ID to Encyrpt and Switch Root Volumes')
    return parser.parse_args()


def connection(region_name='us-west-2', profile_name='default'):
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    client = session.client('ec2')
    resource = session.resource('ec2')
    return client, resource


def get_root_volume(resource, instance_id):
    instance = resource.Instance(id=instance_id)

    print("[I] Determining Current Root Volume")
    for vol_data in instance.block_device_mappings:
        if 'sda' in vol_data['DeviceName'] or 'xvda' in vol_data['DeviceName']:
            volume = resource.Volume(vol_data['Ebs']['VolumeId'])
            if not volume.encrypted:
                return volume
            else:
                print(f'[√] Volume: {volume.id} Already Encrypted')
                sys.exit() 
                return False


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


def create_snapshot(client, resource, volume_id):
    waiter = client.get_waiter('snapshot_completed')
    snap_response = client.create_snapshot(VolumeId=volume_id)
    snapshot_id = snap_response['SnapshotId']

    print(f'[I] Starting snapshot of {volume_id}')

    try:
        waiter.wait(SnapshotIds=[snapshot_id])
        print(f'[√] Snapshot: {snapshot_id} Created!')
        return snapshot_id
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False


def copy_snapshot(client, resource, snapshot_id, region_name):
    waiter = client.get_waiter('snapshot_completed')
    snapshot = resource.Snapshot(id=snapshot_id)
    copy_response = snapshot.copy(
            Description='Enable Encryption',
            Encrypted=True,
            SourceRegion=region_name
            )
    new_snapshot_id = copy_response['SnapshotId'] 

    print(f'[I] Copying and Encrypting {new_snapshot_id} from {snapshot_id}')

    try:
        waiter.wait(SnapshotIds=[new_snapshot_id])
        print(f'[√] Encrypted Snapshot Created: {new_snapshot_id} Created!')
        return new_snapshot_id
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False


def create_encrypted_volume(client, resource, instance_id, snapshot_id, region_name):
    waiter = client.get_waiter('volume_available')
    instance_info = resource.Instance(id=instance_id)
    instance_az = instance_info.placement['AvailabilityZone']

    vol_response = client.create_volume(
            AvailabilityZone=instance_az,
            Encrypted=True,
            SnapshotId=snapshot_id)
    volume_id = vol_response['VolumeId']

    print(f'[I] Creating Encrypted Volume: {volume_id} from Snapshot: {snapshot_id}')

    try:
        waiter.wait(VolumeIds=[volume_id])
        print(f'[√] Volume Created: {volume_id}')
        return volume_id
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False



def detach_volume(client, resource, instance_id, volume_id):
    waiter = client.get_waiter('volume_available')
    instance = resource.Instance(id=instance_id)
    response = instance.detach_volume(VolumeId=volume_id)
    volume_id = response['VolumeId']

    print(f'[I] Detaching Volume: {volume_id}')    

    try:
        waiter.wait(VolumeIds=[volume_id])
        print(f'[√] Volume Detached: {volume_id}')
        return True
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False
    

def attach_volume(client, resource, instance_id, volume_id):
    waiter = client.get_waiter('volume_in_use')
    instance = resource.Instance(id=instance_id)
    response = instance.attach_volume(
            VolumeId=volume_id,
            Device='/dev/xvda')
    volume_id = response['VolumeId']

    print(f'[I] Attaching Volume: {volume_id}')    

    try:
        waiter.wait(VolumeIds=[volume_id])
        print(f'[√] Volume Attached: {volume_id}')
        return True
    except botocore.exception.WaiterError as e:
        print(e.message)


def main():
    args = get_args()
    region_name = args.region_name
    
    tic = time.perf_counter()
    print(f"[I] Starting Encryption and the Old Switcheroo on {args.instance_id}'s Root Volume")
    
    client, resource = connection(profile_name=args.profile_name, region_name="us-west-2")
    current_root_volume = get_root_volume(resource, args.instance_id)
    stop_result = stop(client, resource, args.instance_id)

    if stop_result:
        snapshot_id = create_snapshot(client, resource, current_root_volume.id)
    else:
            print(f'[X] Issue Stopping Instance {args.instance_id}')

    if snapshot_id:
        new_snapshot_id = copy_snapshot(client, resource, snapshot_id, args.region_name)

    if new_snapshot_id:
        encrypted_volume = create_encrypted_volume(client, resource, args.instance_id, new_snapshot_id, args.region_name)
    
    if encrypted_volume:
        detach_response = detach_volume(client, resource, args.instance_id, current_root_volume.id)
    
    if detach_response:
        attach_response = attach_volume(client, resource, args.instance_id, encrypted_volume)

    if attach_response: 
        start(client, resource, args.instance_id)

    toc = time.perf_counter()
    print(f'***** All Tasks Finished in: {(toc-tic)/60:0.2f} minutes *****')


if '__main__' in __name__:
    main()
