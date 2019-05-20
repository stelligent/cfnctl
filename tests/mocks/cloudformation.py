class Cloudformation:
    def __init__(self):
        self.mocks = {}
        self.called = {
            'describe_stacks': 0,
            'describe_stack_events': 0,
            'create_change_set': 0,
            'describe_change_set': 0,
            'execute_change_set': 0,
        }

    def mock(self, method, callback):
        if method not in self.mocks:
            self.mocks[method] = []
        self.mocks[method].append(callback)

    def increment_and_get_callback(self, method):
        self.called[method] += 1
        if method not in self.mocks:
            raise Exception('no mocks for %s' % method)
        callback = self.mocks[method].pop(0)
        return callback

    def describe_stacks(self, StackName):
        callback = self.increment_and_get_callback('describe_stacks')
        return callback(StackName)

    def describe_stack_events(self, StackName, NextToken=None):
        callback = self.increment_and_get_callback('describe_stack_events')
        return callback(StackName, NextToken)

    def execute_change_set(self, ChangeSetName, StackName):
        callback = self.increment_and_get_callback('execute_change_set')
        return callback(ChangeSetName, StackName)

    def create_change_set(
        self,
        StackName,
        TemplateURL,
        UsePreviousTemplate,
        Parameters,
        Capabilities,
        ChangeSetName,
        ChangeSetType):
            callback = self.increment_and_get_callback('create_change_set')
            return callback(StackName, TemplateURL, UsePreviousTemplate, Parameters, Capabilities, ChangeSetName, ChangeSetType)

    def describe_change_set(self, ChangeSetName, StackName):
        callback = self.increment_and_get_callback('describe_change_set')
        return callback(ChangeSetName, StackName)



def make_describe_stacks(client, n_calls, complete_status='CREATE_COMPLETE', stack_name_override=None):
    def describe_stacks(StackName):
        StackName = stack_name_override or StackName
        status = 'CREATE_IN_PROGRESS'
        if client.called['describe_stacks'] == n_calls:
            status = complete_status
        else:
            client.mock('describe_stacks', describe_stacks)
        return {
            'Stacks': [
                {
                    'StackName': StackName,
                    'StackStatus': status
                }
            ],
            'NextToken': 'string'
        }
    return describe_stacks

def make_describe_stack_events(client, n_calls):
    def describe_stack_events(StackName, NextToken):
        # mock the call again
        if client.called['describe_stack_events'] == n_calls:
            return {'StackEvents': []}
        client.mock('describe_stack_events', describe_stack_events)
        return {
            'StackEvents': [
                {
                    'LogicalResourceId': StackName,
                    'ResourceStatus': 'CREATE_IN_PROGRESS', 
                    'ResourceStatusReason': 'User Initiated', 
                    'StackName': StackName, 
                    'EventId': 1
                }, 
                {
                    'LogicalResourceId': StackName,
                    'ResourceStatus': 'REVIEW_IN_PROGRESS',
                    'ResourceStatusReason': 'User Initiated', 
                    'StackName': StackName,
                    'EventId': 2
                }
            ]
        }
    return describe_stack_events

def make_describe_change_set(client, n_calls, status='CREATE_COMPLETE'):
    def describe_change_set(StackName, NextToken):
        # mock the call again
        if client.called['describe_change_set'] == n_calls:
            return {
                'StackName': StackName,
                'Status': status,
            }
        client.mock('describe_change_set', describe_change_set)
        return {
            'StackName': StackName,
            'Status': 'CREATE_IN_PROGRESS',
        }

    return describe_change_set
