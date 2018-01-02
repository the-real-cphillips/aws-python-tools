# aws-python-tools
Just some AWS Python tools I've written.

* `elb_ssl_swap.py` - Quick tool to allow you to change the SSL Cert on an ELB
  * You'll need:
    * AWS Account Number
    * Listener Port Number
    * ACM Certificate ID (Not the whole ARN)
    * ELB Name
    * Region (ie us-west-2, us-east-1, etc) 
