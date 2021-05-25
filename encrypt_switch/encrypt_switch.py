#!/usr/bin/env python
import argparse
import boto3
import botocore
import concurrent.futures
import sys
import threading
import time
from colorama import Fore, Back, Style


def get_args():
    parser = argparse.ArgumentParser(
            description="Encrypt and Switch ALL Attached EBS Volumes!",
            epilog="Not a Bait and Switch")
    parser.add_argument('-p', '--profile_name',
                        action='store',
                        dest='profile_name',
                        default='default',
                        help='AWS Profile Name')
    parser.add_argument('-r', '--region_name',
                        action='store',
                        dest='region_name',
                        default='us-east-2',
                        help='AWS Region')
    parser.add_argument('-i', '--instance-id',
                       action='store',
                       required=True,
                       dest='instance_id',
                       help='Instance ID to Encrypt and Switch EBS Volumes')
    return parser.parse_args()


def connection(region_name='us-east-2', profile_name='default'):
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    client = session.client('ec2')
    resource = session.resource('ec2')
    return client, resource


def get_volumes(resource, instance_id):
    volume_list = []

    instance = resource.Instance(id=instance_id)
    tags = [ tag['Value'] for tag in instance.tags if tag['Key'] == 'Name' ]
    print(f'[I] Finding Volumes for Instance: {tags[0]}')
    volumes = instance.volumes.all()

    for volume in volumes:
        if not volume.encrypted:
            for data in volume.attachments:
                volume_data = resource.Volume(id=data['VolumeId'])
                volume_list.append(volume_data)
                print(Fore.RED + f'[X] Volume {volume.id} Needs To Be Encrypted!' + Fore.WHITE)
        else:
            print(Fore.GREEN + f'[√] Volume {volume.id} Already Encrypted!' + Fore.WHITE)
    return volume_list


def stop(client, resource, instance_id):
    waiter = client.get_waiter('instance_stopped')
    instance = resource.Instance(id=instance_id)
    instance.stop()

    print(f'[I] Attempting to Stop {instance.id}')

    try:
        waiter.wait(InstanceIds=[instance.id])
        print(Fore.GREEN + f'[√] {instance.id} Stopped\n' + Fore.WHITE)
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
        print(Fore.GREEN + f'[√] {instance.id} Running\n' + Fore.WHITE)
        return True
    except botocore.exceptions.WaiterError as e:
        print(e.message)
        return False


def create_snapshot(client, resource, volume_id, device_name, instance_name):
    waiter = client.get_waiter('snapshot_completed')
    snap_response = client.create_snapshot(
            VolumeId=volume_id,
            Description=f'{instance_name} - {device_name}')
    snapshot_id = snap_response['SnapshotId']

    print(f'[I] Starting snapshot of {volume_id} ({device_name})')

    try:
        waiter.wait(SnapshotIds=[snapshot_id])
        print(Fore.GREEN + f'[√] Snapshot: {snapshot_id} Created!\n' + Fore.WHITE)
        return snapshot_id
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False


def copy_snapshot(client, resource, snapshot_id, region_name, device_name, instance_name):
    waiter = client.get_waiter('snapshot_completed')
    snapshot = resource.Snapshot(id=snapshot_id)
    copy_response = snapshot.copy(
            Description=f'Enable Encryption - {instance_name} - {device_name}',
            Encrypted=True,
            SourceRegion=region_name
            )
    new_snapshot_id = copy_response['SnapshotId'] 

    print(f'[I] Copying and Encrypting {new_snapshot_id} from {snapshot_id}')

    try:
        waiter.wait(SnapshotIds=[new_snapshot_id])
        print(Fore.GREEN + f'[√] Encrypted Snapshot Created: {new_snapshot_id} Created!\n' + Fore.WHITE)
        return new_snapshot_id
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False


def create_encrypted_volume(client, resource, snapshot_id, region_name, instance_name, volume):
    waiter = client.get_waiter('volume_available')
    device_name = volume.attachments[0]['Device']
    

    if 'io' in volume.volume_type or 'gp3' == volume.volume_type:
        vol_response = client.create_volume(
            AvailabilityZone=volume.availability_zone,
            Encrypted=True,
            Iops=volume.iops,
            VolumeType=volume.volume_type,
            SnapshotId=snapshot_id,
            TagSpecifications=[
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': f'{instance_name} - {device_name}'
                        }
                    ]
                }
            ])
    else:
        vol_response = client.create_volume(
            AvailabilityZone=volume.availability_zone,
            Encrypted=True,
            SnapshotId=snapshot_id,
            TagSpecifications=[
                {
                    'ResourceType': 'volume',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': f'{instance_name} - {device_name}'
                        }
                    ]
                }
            ])
    volume_id = vol_response['VolumeId']

    print(f'[I] Creating Encrypted Volume: {volume_id} from Snapshot: {snapshot_id}')

    try:
        waiter.wait(VolumeIds=[volume_id])
        print(Fore.GREEN + f'[√] Volume Created: {volume_id}\n' + Fore.WHITE)
        return volume_id
    except botocore.exception.WaiterError as e:
        print(e.message)
        return False



def detach_volume(client, resource, instance_id, volume_id, device_name):
    waiter = client.get_waiter('volume_available')
    instance = resource.Instance(id=instance_id)
    response = instance.detach_volume(VolumeId=volume_id)
    volume_id = response['VolumeId']

    print(f'[I] Detaching Volume: {volume_id} --> {device_name}')    

    try:
        waiter.wait(VolumeIds=[volume_id])
        print(Fore.GREEN + f'[√] Volume Detached: {volume_id}\n' + Fore.WHITE)
        return True
    except (botocore.exception.WaiterError, botocore.exceptions.ClientError) as e:
        print(e.message)
        return False
    

def attach_volume(client, resource, instance_id, volume_id, device_name):
    waiter = client.get_waiter('volume_in_use')
    instance = resource.Instance(id=instance_id)
    response = instance.attach_volume(
            VolumeId=volume_id,
            Device=device_name)
    volume_id = response['VolumeId']

    print(f'[I] Attaching Volume: {volume_id} --> {device_name}')    

    try:
        waiter.wait(VolumeIds=[volume_id])
        print(Fore.GREEN + f'[√] Volume Attached: {volume_id}\n' + Fore.WHITE)
        return True
    except (botocore.exception.WaiterError, botocore.exceptions.ClientError) as e:
        print(e.message)
        return False


def swap(client, resource, region_name, volume, instance_id):
        current_thread = threading.current_thread()
        print(Fore.GREEN + f'##### {current_thread.name} Starting Swap of {volume.id} #####' + Fore.WHITE)

        vol_tic = time.perf_counter()
        instance = resource.Instance(id=instance_id)

        instance_name = [ tag['Value'] for tag in instance.tags if tag['Key'] == 'Name' ][0]
        device_name = volume.attachments[0]['Device']

        try:
            detach_response = detach_volume(client, resource, instance_id, volume.id, device_name)
            snapshot_id = create_snapshot(client, resource, volume.id, device_name, instance_name)
            new_snapshot_id = copy_snapshot(client, resource, snapshot_id, region_name, device_name, instance_name)
            encrypted_volume = create_encrypted_volume(client, resource, new_snapshot_id, region_name, instance_name, volume)
            attach_response = attach_volume(client, resource, instance_id, encrypted_volume, device_name)
            vol_toc = time.perf_counter()
            print(Fore.GREEN + f'##### {current_thread.name} Completed Actions on {volume.id} in {(vol_toc-vol_tic)/60:.0f} minutes #####\n' + Fore.WHITE)
        except:
            print(Fore.RED + f'{current_thread.name} [X] Reattaching {volume.id} --> {device_name}' + Fore.WHITE)
            attach_volume(client, resource, instance_id, volume.id, device_name)



def main():
    args = get_args()
    tic = time.perf_counter()

    print(Fore.GREEN + f"[I] Starting Encryption and the Switch on {args.instance_id}'s Volumes\n" + Style.RESET_ALL)
    client, resource = connection(profile_name=args.profile_name, region_name=args.region_name)
    current_volumes = get_volumes(resource, args.instance_id)


    if len(current_volumes) > 0:
        stop(client, resource, args.instance_id)
    else:
        print(Fore.GREEN + f'[√] All Volumes Encrypted!' + Style.RESET_ALL)
        sys.exit()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="THREAD") as executor:
        futures = []
        for volume in current_volumes:
            futures.append(executor.submit(swap, client, resource, args.region_name, volume, args.instance_id))

    start(client, resource, args.instance_id)

    toc = time.perf_counter()
    print(Fore.GREEN + f'***** All Tasks Finished in: {(toc-tic)/60:.0f} minutes *****' + Style.RESET_ALL)


if '__main__' in __name__:
    main()
