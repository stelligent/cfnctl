from botocore.exceptions import ClientError

class MockResponse:
    '''
    Class to Mock urllib3 response
    '''
    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def __iter__(self) -> any:
        '''
        Need to implement iterable in order to be representable
        '''
        for value in [self, self.body]:
            yield value

    def __repr__(self) -> (any, str):
        '''
        Overload the representation of the object for
        assigning values from this class when destructuring
        '''
        return repr([self, self.body])

def boto_client_error(code: str, method: str, message: str = 'an error occured'):
    '''
    Create a boto3 ClientError
    '''
    return ClientError(
        {
            'Error': {
                'Code': code,
                'Message': message,
            },
        },
        method,
    )

def mock_change_set(iterations: int, stack_name: str, end_state: str = 'CREATE_COMPLETE'):
    def res():
        return MockResponse(
            200,
            {
                'StackName': stack_name,
                'Status': 'CREATE_IN_PROGRESS',
            },
        )
    steps = [ res() for i in range(iterations - 1) ]
    steps.append(MockResponse(
        200,
        {
            'StackName': stack_name,
            'Status': end_state,
        },
    ))
    return steps

def mock_wait_for_stack(iterations: int, stack_name: str, end_state: str = 'CREATE_COMPLETE'):
    steps = []

    for i in range(1, iterations+1):
        # Get stack events
        steps.append(MockResponse(
            200,
            {
                'StackEvents': [
                    {
                        'LogicalResourceId': stack_name,
                        'ResourceStatus': 'CREATE_IN_PROGRESS',
                        'ResourceStatusReason': 'User Initiated',
                        'StackName': stack_name,
                        'EventId': i
                    },
                ]
            },
        ))
        # Describe stack to get state
        steps.append(MockResponse(
            200,
            {
                'Stacks': [
                    {
                        'StackName': stack_name,
                        'StackStatus': end_state if i is iterations else 'CREATE_IN_PROGRESS'
                    }
                ],
                'NextToken': 'string'
            },
        ))
    return steps
