# S3 Bucket Metric Finder

Pull Metrics from Cloudwatch for an S3 Bucket
## USAGE

```
usage: s3Metrics.py [-h] (-b BUCKET_NAME | -f FILENAME) [-d DAYS]
                    [-m METRIC_NAME] [-s STORAGE_TYPE] [-p PROFILE_NAME]

Find S3 Metrics from Cloudwatch

optional arguments:
  -h, --help            show this help message and exit
  -b BUCKET_NAME, --bucket-name BUCKET_NAME
                        Name of an S3 Bucket
  -f FILENAME, --filename FILENAME
                        Name of file containing bucket names one per line.
  -d DAYS, --days DAYS  Number of "Days ago" to pull datapoints from
                        Default: 2
  -m METRIC_NAME, --metric-name METRIC_NAME
                        Type of Metric to check for:
                        BucketSizeBytes | NumberOfObjects
                        Default: BucketSizeBytes
  -s STORAGE_TYPE, --storage-type STORAGE_TYPE
                        Type of Storage to check for:
                        StandardStorage | StandardIAStorage | ReducedRedundancyStorage | AllStorageTypes
                        Default: StandardStorage
  -p PROFILE_NAME, --profile-name PROFILE_NAME
                        Use different profile in ~/.aws/credentials: default is named default
k

```
