class Cloudformation:
    def __init__(self):
        self.mocks = {}
        self.called = {
            'describe_stacks': 0,
            'describe_stack_events': 0
        }

    def mock(self, method, callback):
        if method not in self.mocks:
            self.mocks[method] = []
        self.mocks[method].append(callback)

    def describe_stacks(self, StackName):
        self.called['describe_stacks'] += 1
        if 'describe_stacks' not in self.mocks:
            raise Exception('no mocks for describe_stacks')
        callback = self.mocks['describe_stacks'].pop(0)
        return callback(StackName)

    def describe_stack_events(self, StackName, NextToken=None):
        self.called['describe_stack_events'] += 1
        if 'describe_stack_events' not in self.mocks:
            raise Exception('no mocks for describe_stack_events')
        callback = self.mocks['describe_stack_events'].pop(0)
        return callback(StackName, NextToken)
