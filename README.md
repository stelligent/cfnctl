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
usage: cfnctl [-h] [-p AWS_PROFILE] [-r REGION] {deploy} ...

Launch and manage CloudFormation stacks

optional arguments:
  -h, --help      show this help message and exit
  -p AWS_PROFILE  AWS Profile
  -r REGION       Region name

subcommands:
  command to run

  {deploy}
    deploy        creates a changeset and executes to create or update stack
```
