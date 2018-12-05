import unittest
import cfnctl.commands.deploy as deploy

class TestDeploy(unittest.TestCase):

    def test_template_url(self):
        url = deploy._get_template_url('foo', 'bar.template')
        self.assertEqual(url, 'https://s3.amazonaws.com/foo/bar.template')

    # def test_isupper(self):
    #     self.assertTrue('FOO'.isupper())
    #     self.assertFalse('Foo'.isupper())

    # def test_split(self):
    #     s = 'hello world'
    #     self.assertEqual(s.split(), ['hello', 'world'])
    #     # check that s.split fails when the separator is not a string
    #     with self.assertRaises(TypeError):
    #         s.split(2)

if __name__ == '__main__':
    unittest.main()
