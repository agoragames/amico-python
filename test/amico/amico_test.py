import unittest
import time
import sure

from redis import Redis
from amico import Amico

class AmicoTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_version(self):
    Amico.VERSION.should.equal('1.0.0')
