import unittest
from utils import validate_discard

class TestDiscardValidation(unittest.TestCase):
    def test_pair_discard(self):
        params = [[3,3], 'triple']
        self.assertEqual(validate_discard(*params), '1-pairs')
    
    def test_single_discard(self):
            params = [[3], 'triple']
            self.assertEqual(validate_discard(*params), '1-singles')

    def test_two_pairs_discard(self):
        params = [[3,3,4,4], 'quad']
        self.assertEqual(validate_discard(*params), '2-pairs')

    def test_two_singles_discard(self):
        params = [[3,4], 'quad']
        self.assertEqual(validate_discard(*params), '2-singles')

    def test_double_discard_triple(self):
        params = [[3,4], 'triple']
        self.assertEqual(validate_discard(*params), False)
                
    def test_mix_single_and_pair(self):
        params = [[3,3,4], 'quad']
        self.assertEqual(validate_discard(*params), False)