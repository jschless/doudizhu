import unittest
from utils import validate_type

class TestHandValidation(unittest.TestCase):
    def test_single(self):
        params = list(range(3,18))
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type([p]), 'single')

    def test_double(self):
        params = list(range(3,16))
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type([p, p]), 'pair')

    def test_triple(self):
        params = list(range(3,16))
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type([p, p, p]), 'triple')

    def test_quad(self):
        params = list(range(3,16))
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type([p, p, p, p]), 'quad')

    def test_joker_bomb(self):
        self.assertEqual(validate_type([16,17]), 'rocket')

    def test_two_airplane(self):
        params = []
        for i in range(3, 13):
            temp_list = [i]*3
            for j in [1]:
                temp_list += [i+j]*3
            params.append(temp_list)

        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '2-airplane')

    def test_three_airplane(self):
        params = []
        for i in range(3, 12):
            temp_list = [i]*3
            for j in [1, 2]:
                temp_list += [i+j]*3
            params.append(temp_list)

        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '3-airplane')

    def test_three_pair_straight(self):
        params = [[3,3,4,4,5,5], [10,10,11,11,12,12]]
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '3-pair-straight')

    def test_five_pair_straight(self):
        params = [[3,3,4,4,5,5,6,6,7,7], [10,10,11,11,12,12,13,13,14,14]]
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '5-pair-straight')


    def test_five_straight(self):
        params = [list(range(i, i+5)) for i in range(3, 11)]
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '5-straight')

    def test_six_straight(self):
        params = [list(range(i, i+6)) for i in range(3, 10)]
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '6-straight')

    def test_seven_straight(self):
        params = [list(range(i, i+7)) for i in range(3, 9)]
        for p in params:
            with self.subTest():
                self.assertEqual(validate_type(p), '7-straight')

    def test_straight_with_two(self):
        cards = [11,12,13,14,15]
        self.assertNotEqual(validate_type(cards), '5-straight')
        self.assertEqual(validate_type(cards), False)


if __name__ == '__main__':
    unittest.main()