class S3:
    def __init__(self):
        self.mocks = {}
        self.called = {
            'upload_file': 0,
        }

    def mock(self, method, callback):
        if method not in self.mocks:
            self.mocks[method] = []
        self.mocks[method].append(callback)

    def upload_file(self, file_path, bucket, template_name):
        self.called['upload_file'] += 1
        if 'upload_file' not in self.mocks:
            raise Exception('no mocks for upload_file')
        callback = self.mocks['upload_file'].pop(0)
        return callback(file_path, bucket, template_name)
