class S3:
    def __init__(self):
        self.mocks = {}
        self.called = {
            'upload_file': 0,
            'list_buckets': 0,
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

    def upload_file(self, file_path, bucket, template_name):
        callback = self.increment_and_get_callback('upload_file')
        return callback(file_path, bucket, template_name)

    def list_buckets(self):
        callback = self.increment_and_get_callback('list_buckets')
        return callback()
