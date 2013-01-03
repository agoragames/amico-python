import unittest
import time
import sure

import redis
from amico import Amico

class AmicoTest(unittest.TestCase):
  def setUp(self):
    self.redis_connection = redis.StrictRedis(host = 'localhost', port = 6379, db = 15)

  def tearDown(self):
    self.redis_connection.flushdb()

  def test_version(self):
    Amico.VERSION.should.equal('1.0.0')

  def test_amico_defaults(self):
    Amico.DEFAULTS['namespace'].should.equal('amico')
    Amico.DEFAULTS['following_key'].should.equal('following')
    Amico.DEFAULTS['followers_key'].should.equal('followers')
    Amico.DEFAULTS['blocked_key'].should.equal('blocked')
    Amico.DEFAULTS['blocked_by_key'].should.equal('blocked_by')
    Amico.DEFAULTS['reciprocated_key'].should.equal('reciprocated')
    Amico.DEFAULTS['pending_key'].should.equal('pending')
    Amico.DEFAULTS['pending_with_key'].should.equal('pending_with')
    Amico.DEFAULTS['pending_follow'].should.be.false
    Amico.DEFAULTS['default_scope_key'].should.equal('default')
    Amico.DEFAULTS['page_size'].should.equal(25)

  # follow tests
  def test_it_should_allow_you_to_follow(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['followers_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(1)

  def test_it_should_not_allow_you_to_follow_yourself(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 1)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['followers_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(0)

  def test_it_should_add_each_individual_to_the_reciprocated_set_if_you_both_follow_each_other(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(11, 1)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['reciprocated_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['reciprocated_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(1)

  # pending follow tests
  def test_it_should_remove_the_pending_relationship_and_add_to_following_and_followers_if_accept_is_called(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.is_pending(1, 11).should.be.true
    amico.is_pending_with(11, 1).should.be.true

    amico.accept(1, 11)

    amico.is_pending(1, 11).should.be.false
    amico.is_pending_with(11, 1).should.be.false
    amico.is_following(1, 11).should.be.true
    amico.is_following(11, 1).should.be.false
    amico.is_follower(11, 1).should.be.true
    amico.is_follower(1, 11).should.be.false

  # unfollow tests
  def test_it_should_allow_you_to_unfollow(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['followers_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(1)

    amico.unfollow(1, 11)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['followers_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['reciprocated_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['reciprocated_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)

  # block tests
  def test_it_should_allow_you_to_block_someone_following_you(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(11, 1)
    amico.block(1, 11)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_by_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(1)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['reciprocated_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['reciprocated_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)

  def test_it_should_allow_you_to_block_someone_who_is_not_following_you(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(1, 11)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_by_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(1)

  def test_it_should_not_allow_someone_you_have_blocked_to_follow_you(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(1, 11)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)

    amico.follow(11, 1)

    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['following_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_key'], Amico.DEFAULTS['default_scope_key'], 1)).should.equal(1)

  def test_it_should_not_allow_you_to_block_yourself(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(1, 1)

    amico.is_blocked(1, 1).should.be.false

  # unblock tests
  def test_it_should_allow_you_to_block_someone_you_have_blocked(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(1, 11)
    amico.is_blocked(1, 11).should.be.true
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_by_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(1)
    amico.unblock(1, 11)
    amico.is_blocked(1, 11).should.be.false
    amico.redis_connection.zcard('%s:%s:%s:%s' % (Amico.DEFAULTS['namespace'], Amico.DEFAULTS['blocked_by_key'], Amico.DEFAULTS['default_scope_key'], 11)).should.equal(0)

  # deny tests
  def test_it_should_remove_the_pending_relationship_without_following_or_blocking(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.is_pending(1, 11).should.be.true
    amico.is_pending_with(11, 1).should.be.true

    amico.deny(1, 11)

    amico.is_following(1, 11).should.be.false
    amico.is_pending(1, 11).should.be.false
    amico.is_pending_with(11, 1).should.be.false
    amico.is_blocked(1, 11).should.be.false