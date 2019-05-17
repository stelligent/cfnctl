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
