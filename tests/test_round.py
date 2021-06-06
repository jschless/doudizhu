import unittest
from player import Player 
from round import Round 

class TestSimpleRound(unittest.TestCase):
    def test_bidding(self):
        p1 = Player('Joe', test=True)
        p2 = Player('Matt', test=True)
        p3 = Player('Zade', test=True)
        r = Round([p1,p2,p3])
        self.assertEqual(r.run_bidding(), 1)