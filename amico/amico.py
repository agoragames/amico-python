import redis

class Amico(object):
  VERSION = '1.0.0'

  DEFAULTS = {
    'namespace': 'amico',
    'following_key': 'following',
    'followers_key': 'followers',
    'blocked_key': 'blocked',
    'blocked_by_key': 'blocked_by',
    'reciprocated_key': 'reciprocated',
    'pending_key': 'pending',
    'pending_with_key': 'pending_with',
    'pending_follow': False,
    'default_scope_key': 'default',
    'page_size': 25
  }

  def __init__(self, options = DEFAULTS, redis_connection = None):
    self.options = Amico.DEFAULTS.copy()
    self.options.update(options)
    if redis_connection == None:
      self.redis_connection = redis.StrictRedis(host = 'localhost', port = 6379, db = 0)
    else:
      self.redis_connection = redis_connection

  def follow(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return
    if self.is_blocked(to_id, from_id, scope):
      return
    if self.options['pending_follow'] and self.is_pending(from_id, to_id, scope):
      return

    if self.options['pending_follow']:
      transaction = self.redis_connection.pipeline()
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), 33, from_id)
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), 33, to_id)
      transaction.execute()
    else:
      self.__add_following_followers_reciprocated(from_id, to_id, scope)

  def unfollow(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    transaction = self.redis_connection.pipeline()
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), to_id)
    transaction.execute()

  def block(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    transaction = self.redis_connection.pipeline()
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, to_id), from_id)
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, from_id), 33, to_id)
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, to_id), 33, from_id)
    transaction.execute()

  def unblock(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    transaction = self.redis_connection.pipeline()
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, to_id), from_id)
    transaction.execute()

  def accept(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    self.__add_following_followers_reciprocated(from_id, to_id, scope)

  def deny(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    transaction = self.redis_connection.pipeline()
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), to_id)
    transaction.execute()

  def clear(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    # no longer following (or followed by) anyone
    self.__clear_bidirectional_sets_for_id(id, self.options['following_key'], self.options['followers_key'], scope)
    self.__clear_bidirectional_sets_for_id(id, self.options['followers_key'], self.options['following_key'], scope)
    self.__clear_bidirectional_sets_for_id(id, self.options['reciprocated_key'], self.options['reciprocated_key'], scope)
    # no longer blocked by (or blocking) anyone
    self.__clear_bidirectional_sets_for_id(id, self.options['blocked_by_key'], self.options['blocked_key'], scope)
    self.__clear_bidirectional_sets_for_id(id, self.options['blocked_key'], self.options['blocked_by_key'], scope)
    # no longer pending with anyone (or have any pending followers)
    self.__clear_bidirectional_sets_for_id(id, self.options['pending_with_key'], self.options['pending_key'], scope)
    self.__clear_bidirectional_sets_for_id(id, self.options['pending_key'], self.options['pending_with_key'], scope)

  def is_blocked(self, id, blocked_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, id), blocked_id) != None

  def is_follower(self, id, follower_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, id), follower_id) != None

  def is_following(self, id, following_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, id), following_id) != None

  def is_reciprocated(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.is_following(from_id, to_id, scope) and self.is_following(to_id, from_id, scope)

  def is_pending(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), from_id) != None

  def is_pending_with(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, to_id), from_id) != None

  def following_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, id))

  def followers_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, id))

  def blocked_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, id))

  def blocked_by_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, id))

  def reciprocated_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, id))

  def pending_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, id))

  def pending_with_count(self, id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, id))

  def __clear_bidirectional_sets_for_id(self, id, source_set_key, related_set_key, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    related_ids = self.redis_connection.zrange('%s:%s:%s:%s' % (self.options['namespace'], source_set_key, scope, id), 0, -1)
    transaction = self.redis_connection.pipeline()
    for related_id in related_ids:
      self.redis_connection.zrem('%s:%s:%s:%s' % (self.options['namespace'], related_set_key, scope, related_id), id)
    transaction.execute()

    self.redis_connection.delete('%s:%s:%s:%s' % (self.options['namespace'], source_set_key, scope, id))

  def __add_following_followers_reciprocated(self, from_id, to_id, scope = None):
    if scope == None:
      scope = self.options['default_scope_key']

    transaction = self.redis_connection.pipeline()
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, from_id), 33, to_id)
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, to_id), 33, from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), 33, from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), 33, to_id)
    transaction.execute()

    if self.is_reciprocated(from_id, to_id):
      transaction = self.redis_connection.pipeline()
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, from_id), 33, to_id)
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, to_id), 33, from_id)
      transaction.execute()
