import os
import unittest
import datetime
import test.mocks.cloudformation as cfn
from test.mocks.s3 import S3
from cfnctl.commands.deploy import _wait_for_stack, _stack_exists, _make_change_set, _wait_for_changeset, _stack_complete, _execute_changeset, _get_parameters

class TestCommandDeploy(unittest.TestCase):

    def test_wait_for_stack(self):
        '''pause execution until the stack creation is complete
        '''
        n_calls = 3
        client = cfn.Cloudformation()

        describe_stack_events = cfn.make_describe_stack_events(client, n_calls)
        describe_stacks = cfn.make_describe_stacks(client, n_calls, 'CREATE_COMPLETE')

        client.mock('describe_stack_events', describe_stack_events)
        client.mock('describe_stacks', describe_stacks)
        _wait_for_stack(client, 'foo')
        self.assertEqual(client.called['describe_stack_events'], n_calls)
        self.assertEqual(client.called['describe_stacks'], n_calls)
        # we're only testing that this runs to completion
        self.assertEqual(True, True)

    def test_stack_exists(self):
        '''verify a stack exists
        '''
        client = cfn.Cloudformation()

        describe_stacks = cfn.make_describe_stacks(client, 3, 'CREATE_COMPLETE')
        client.mock('describe_stacks', describe_stacks)

        exists = _stack_exists(client, 'foo')
        self.assertEqual(client.called['describe_stacks'], 1)
        self.assertEqual(exists, True)

    def test_stack_not_exists(self):
        '''verify a stack exists
        '''
        client = cfn.Cloudformation()

        describe_stacks = cfn.make_describe_stacks(client, 3, 'CREATE_COMPLETE', 'bar')
        client.mock('describe_stacks', describe_stacks)

        exists = _stack_exists(client, 'foo')
        self.assertEqual(client.called['describe_stacks'], 1)
        self.assertEqual(exists, False)

    def test_make_create_change_set(self):
        '''create a changeset
        '''
        stack_name = 'foo'
        client = cfn.Cloudformation()

        describe_stacks = cfn.make_describe_stacks(client, 3, 'CREATE_COMPLETE', 'bar')
        client.mock('describe_stacks', describe_stacks)

        def create_change_set(StackName, TemplateURL, UsePreviousTemplate, Parameters, Capabilities, ChangeSetName, ChangeSetType):
            self.assertEqual(ChangeSetType, 'CREATE')
            return {
                'Id': 'string',
                'StackId': 'string'
            }
        client.mock('create_change_set', create_change_set)
        _make_change_set(client, stack_name, '', {})
        self.assertEqual(client.called['create_change_set'], 1)

    def test_make_update_change_set(self):
        '''update a stack with changeset
        '''
        stack_name = 'foo'
        client = cfn.Cloudformation()

        describe_stacks = cfn.make_describe_stacks(client, 3, 'CREATE_COMPLETE')
        client.mock('describe_stacks', describe_stacks)

        def create_change_set(StackName, TemplateURL, UsePreviousTemplate, Parameters, Capabilities, ChangeSetName, ChangeSetType):
            self.assertEqual(ChangeSetType, 'UPDATE')
            return {
                'Id': 'string',
                'StackId': 'string'
            }
        client.mock('create_change_set', create_change_set)
        _make_change_set(client, stack_name, '', {})
        self.assertEqual(client.called['create_change_set'], 1)

    def test_wait_for_changeset(self):
        '''pause execution until the changeset creation is complete
        '''
        n_calls = 3
        client = cfn.Cloudformation()

        describe_change_set = cfn.make_describe_change_set(client, n_calls, 'CREATE_COMPLETE')

        client.mock('describe_change_set', describe_change_set)
        finished = _wait_for_changeset(client, 'foo', 'bar')
        self.assertEqual(client.called['describe_change_set'], n_calls)
        # we're only testing that this runs to completion
        self.assertEqual(finished, True)

    def test_wait_for_changeset_failed(self):
        '''pause execution until the changeset creation is complete
        '''
        n_calls = 1
        client = cfn.Cloudformation()

        describe_change_set = cfn.make_describe_change_set(client, n_calls, 'FAILED')

        client.mock('describe_change_set', describe_change_set)
        finished = _wait_for_changeset(client, 'foo', 'bar')
        self.assertEqual(client.called['describe_change_set'], n_calls)
        # we're only testing that this runs to completion
        self.assertEqual(finished, False)

    def test_stack_complete(self):
        '''Check if the stack status is in a complete state
        '''
        client = cfn.Cloudformation()
        describe_stacks = cfn.make_describe_stacks(client, 1, 'CREATE_COMPLETE', 'foo')
        client.mock('describe_stacks', describe_stacks)
        stack_status = _stack_complete(client, 'foo')
        self.assertEqual(client.called['describe_stacks'], 1)
        self.assertEqual(stack_status['complete'], True)

        client = cfn.Cloudformation()
        describe_stacks = cfn.make_describe_stacks(client, 1, 'UPDATE_ROLLBACK_FAILED')
        client.mock('describe_stacks', describe_stacks)
        stack_status = _stack_complete(client, 'foo')
        self.assertEqual(client.called['describe_stacks'], 1)
        self.assertEqual(stack_status['complete'], True)

    def test_execute_changeset(self):
        '''Check that execute changeset gets called
        '''
        client = cfn.Cloudformation()
        def execute_change_set(ChangeSetName, StackName):
            return {}

        client.mock('execute_change_set', execute_change_set)
        _execute_changeset(client, 'foo', 'bar')
        self.assertEqual(client.called['execute_change_set'], 1)

    def test_get_parameters_empty(self):
        # Need to check rendering a template. Loading a template from disk 
        # and rendering should be separated. This is a placeholder
        parameters = _get_parameters(None)
        self.assertEqual(parameters, [])

if __name__ == '__main__':
    unittest.main()
