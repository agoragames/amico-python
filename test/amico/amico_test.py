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

  # clear tests
  def test_it_should_remove_follower_and_following_relationships(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(11, 1)

    amico.following_count(1).should.equal(1)
    amico.followers_count(1).should.equal(1)
    amico.reciprocated_count(1).should.equal(1)
    amico.following_count(11).should.equal(1)
    amico.followers_count(11).should.equal(1)
    amico.reciprocated_count(11).should.equal(1)

    amico.clear(1)

    amico.following_count(1).should.equal(0)
    amico.followers_count(1).should.equal(0)
    amico.reciprocated_count(1).should.equal(0)
    amico.following_count(11).should.equal(0)
    amico.followers_count(11).should.equal(0)
    amico.reciprocated_count(11).should.equal(0)

  def test_it_should_clear_pending_pending_with_relationships(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.pending_count(11).should.equal(1)

    amico.clear(1)

    amico.pending_count(11).should.equal(0)

  def test_it_should_clear_blocked_blocked_by_relationships(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(1, 11)
    amico.blocked_count(1).should.equal(1)
    amico.blocked_by_count(11).should.equal(1)

    amico.clear(11)

    amico.blocked_count(1).should.equal(0)
    amico.blocked_by_count(11).should.equal(0)

  def test_it_should_return_the_correct_following_list(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(1, 12)
    amico.following(1).should.equal(["12", "11"])

  def test_following_should_page_correctly(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico)
    amico.following(1, page_options = {'page': 1, 'page_size': 5}).should.have.length_of(5)
    amico.following(1, page_options = {'page': 1, 'page_size': 10}).should.have.length_of(10)
    amico.following(1, page_options = {'page': 1, 'page_size': 26}).should.have.length_of(25)

  def test_it_should_return_the_correct_followers_list(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(2, 11)
    amico.followers(11).should.equal(["2", "1"])

  def test_it_should_should_return_the_correct_blocked_list(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(1, 11)
    amico.block(1, 12)
    amico.blocked(1).should.equal(["12", "11"])

  def test_it_should_return_the_correct_blocked_by_list(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.block(11, 1)
    amico.block(12, 1)
    amico.blocked_by(1).should.equal(["12", "11"])

  def test_it_should_return_the_correct_reciprocated_list(self):
    amico = Amico(redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(11, 1)
    amico.reciprocated(1).should.equal(["11"])
    amico.reciprocated(11).should.equal(["1"])

  def test_it_should_return_the_correct_pending_list(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(11, 1)
    amico.pending(1).should.equal(["11"])
    amico.pending(11).should.equal(["1"])

  def test_it_should_return_the_correct_pending_with_list(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    amico.follow(1, 11)
    amico.follow(11, 1)
    amico.pending_with(1).should.equal(["11"])
    amico.pending_with(11).should.equal(["1"])

  def test_it_should_return_the_correct_following_page_count(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico)

    amico.following_page_count(1).should.equal(1)
    amico.following_page_count(1, 10).should.equal(3)
    amico.following_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_followers_page_count(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico)

    amico.followers_page_count(1).should.equal(1)
    amico.followers_page_count(1, 10).should.equal(3)
    amico.followers_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_blocked_page_count(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico, block_relationship = True)

    amico.blocked_page_count(1).should.equal(1)
    amico.blocked_page_count(1, 10).should.equal(3)
    amico.blocked_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_blocked_by_page_count(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico, block_relationship = True)

    amico.blocked_by_page_count(1).should.equal(1)
    amico.blocked_by_page_count(1, 10).should.equal(3)
    amico.blocked_by_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_reciprocated_page_count(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico)

    amico.reciprocated_page_count(1).should.equal(1)
    amico.reciprocated_page_count(1, 10).should.equal(3)
    amico.reciprocated_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_pending_page_count(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico)

    amico.pending_page_count(1).should.equal(1)
    amico.pending_page_count(1, 10).should.equal(3)
    amico.pending_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_pending_with_page_count(self):
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico)

    amico.pending_with_page_count(1).should.equal(1)
    amico.pending_with_page_count(1, 10).should.equal(3)
    amico.pending_with_page_count(1, 5).should.equal(5)

  def test_it_should_return_the_correct_count_for_various_types_of_relationships(self):
    amico = Amico(redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico, count = 6)

    amico.count(1, 'following').should.equal(4)
    amico.count(1, 'followers').should.equal(4)
    amico.count(1, 'reciprocated').should.equal(4)

    self.redis_connection.flushdb()
    self.__add_reciprocal_followers(amico, count = 6, block_relationship = True)

    amico.count(1, 'blocked').should.equal(4)
    amico.count(1, 'blocked_by').should.equal(4)

    self.redis_connection.flushdb()
    amico = Amico(options = {'pending_follow': True}, redis_connection = self.redis_connection)
    self.__add_reciprocal_followers(amico, count = 6)

    amico.count(1, 'pending').should.equal(4)

  def __add_reciprocal_followers(self, amico, count = 27, block_relationship = False):
    for outer_index in range(1, count):
      for inner_index in range(1, count):
        if outer_index != inner_index:
          amico.follow(outer_index, inner_index + 1000)
          amico.follow(inner_index + 1000, outer_index)
          if block_relationship:
            amico.block(outer_index, inner_index + 1000)
            amico.block(inner_index + 1000, outer_index)