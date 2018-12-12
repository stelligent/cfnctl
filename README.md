# CFNCTL

Control Cloudformation stack lifecycle. 

### Features

 - Seemlessly supports templates files over 51,000 bytes
 - Create/Update with single command
 - (optional) Processes your template with jinja2 for advanced templating
 - Always creates a changeset

# Install

> requires boto3

**Pip**

```
pip install cfnctl
```

# Usage

```
usage: cfnctl [-h] [-p AWS_PROFILE] [-r REGION] {deploy,lambda} ...

Launch and manage CloudFormation stacks

positional arguments:
  {deploy,lambda}
    deploy         creates a changeset and executes to create or update stack
    lambda         creates an archive and loads it to S3 to create a lambda
                   from

optional arguments:
  -h, --help       show this help message and exit
  -p AWS_PROFILE   AWS Profile
  -r REGION        Region name
```

### Deploy

```
usage: cfnctl deploy [-h] -s STACK_NAME -t TEMPLATE [-b BUCKET] [-nr]
                     [-p PARAMETERS]

optional arguments:
  -h, --help     show this help message and exit

required arguments:
  -s STACK_NAME  Stack name
  -t TEMPLATE    CFN Template from local file or URL

optional arguments:
  -b BUCKET      Bucket to upload template to
  -nr            Do not rollback
  -p PARAMETERS  Local parameters JSON file
```

### Lambda

Package a folder into a zip archive and upload to S3. Creates the bucket
if it does not exist. Outputs the S3 url for use in a stack.

```
usage: cfnctl lambda [-h] -s SOURCE [-o OUTPUT] [-b BUCKET]

optional arguments:
  -h, --help  show this help message and exit

required arguments:
  -s SOURCE   Source folder to zip and upload

optional arguments:
  -o OUTPUT   Destination of the archive file
  -b BUCKET   Bucket to upload archive to
```
