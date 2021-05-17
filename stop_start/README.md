# Instance State Switch

Starts an Instance if it's Stopped.
Stops an Instance if it's Running.


## Usage

```bash
╰─ ./state_switch.py -h
usage: state_switch.py [-h] [-p PROFILE_NAME] [-r REGION_NAME] -i INSTANCE_ID

Switch State of an Instance

optional arguments:
  -h, --help            show this help message and exit
  -p PROFILE_NAME, --profile_name PROFILE_NAME
                        AWS Profile Name
  -r REGION_NAME, --region_name REGION_NAME
                        AWS Region Name
  -i INSTANCE_ID, --instance-id INSTANCE_ID
                        Instance Id

```
