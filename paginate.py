# Paginator thing for boto3 I found just kinda floating around reddit...
# it's really useful in a quick pinch for needing a paginator
def paginate(method, **kwargs):
    client = method.__self__
    paginator = client.get_paginator(method.__name__)
    for page in paginator.paginate(**kwargs).result_key_iters():
        for result in page:
            yield result

# USAGE
s3 = session.client('s3')
for key in paginate(s3.list_objects_v2, Bucket='paginate-example'):
    print(key)
