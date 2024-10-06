import unittest
import os
import pat_resolve

class TestPatResolve(unittest.TestCase):
    def test_handle_exclude_with_testdata(self):
        # list all .txt files in testdata folder
        testdata_folder = "testdata"
        testdata_files = [f for f in os.listdir(testdata_folder) if f.endswith('.txt')]
        for testdata_file in testdata_files:
            print(f"Testing {testdata_file}")
            with open(f"{testdata_folder}/{testdata_file}", 'r') as f:
                file_content = f.read()
            with open(f"{testdata_folder}/{testdata_file+'.expected'}", 'r') as f:
                expected = f.read()
            with open(f"{testdata_folder}/{testdata_file+'.names'}", 'r') as f:
                names = f.read()
            self.assertEqual(pat_resolve.handle_exclude(file_content, names), expected)

if __name__ == '__main__':
    unittest.main()