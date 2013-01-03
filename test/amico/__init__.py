import unittest
from amico_test import AmicoTest

def all_tests():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(AmicoTest))
  return suite
