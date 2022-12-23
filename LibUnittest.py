import unittest
from LibFileOperations import FileOperations_

#setup e teardown sao chamados respectivamente antes e depois de cada teste


class FileOperationsTestes(unittest.TestCase):

    def setUp(self):
        """criacao de classes e incializacao de databases para cada teste, esse método é rodado antes de cada teste"""
        pass

    def teste_file_tree(self):
        self.assertEqual(
            1,
            1         
        )

    def tearDown(self):
        """Destruição das classes e databases utilizadas em cada teste"""
        pass



if __name__ == "__main__":
    unittest.main()