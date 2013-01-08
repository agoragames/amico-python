import math
import time

import redis

class Amico(object):
  VERSION = '1.0.1'

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
    '''
    Initialize a new class for establishing relationships.

    @param options [dictionary] (Default: Amico.DEFAULTS)
    @param redis_connection [redis] (Default: None) Redis connection
    '''
    self.options = Amico.DEFAULTS.copy()
    self.options.update(options)
    if redis_connection == None:
      self.redis_connection = redis.StrictRedis(host = 'localhost', port = 6379, db = 0)
    else:
      self.redis_connection = redis_connection

  def follow(self, from_id, to_id, scope = None):
    '''
    Establish a follow relationship between two IDs. After adding the follow
    relationship, it checks to see if the relationship is reciprocated and establishes that
    relationship if so.

    @param from_id [String] The ID of the individual establishing the follow relationship.
    @param to_id [String] The ID of the individual to be followed.
    @param scope [String] Scope for the call.
    '''
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
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), int(time.time()), from_id)
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), int(time.time()), to_id)
      transaction.execute()
    else:
      self.__add_following_followers_reciprocated(from_id, to_id, scope)

  def unfollow(self, from_id, to_id, scope = None):
    '''
    Remove a follow relationship between two IDs. After removing the follow
    relationship, if a reciprocated relationship was established, it is
    also removed.

    @param from_id [String] The ID of the individual removing the follow relationship.
    @param to_id [String] The ID of the individual to be unfollowed.
    @param scope [String] Scope for the call.
    '''
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
    '''
    Block a relationship between two IDs. This method also has the side effect
    of removing any follower or following relationship between the two IDs.

    @param from_id [String] The ID of the individual blocking the relationship.
    @param to_id [String] The ID of the individual being blocked.
    @param scope [String] Scope for the call.
    '''
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
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, from_id), int(time.time()), to_id)
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, to_id), int(time.time()), from_id)
    transaction.execute()

  def unblock(self, from_id, to_id, scope = None):
    '''
    Unblock a relationship between two IDs.

    @param from_id [String] The ID of the individual unblocking the relationship.
    @param to_id [String] The ID of the blocked individual.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    transaction = self.redis_connection.pipeline()
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, from_id), to_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, to_id), from_id)
    transaction.execute()

  def accept(self, from_id, to_id, scope = None):
    '''
    Accept a relationship that is pending between two IDs.

    @param from_id [String] The ID of the individual accepting the relationship.
    @param to_id [String] The ID of the individual to be accepted.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    self.__add_following_followers_reciprocated(from_id, to_id, scope)

  def deny(self, from_id, to_id, scope = None):
    '''
    Deny a relationship that is pending between two IDs.

    @param from_id [String] The ID of the individual denying the relationship.
    @param to_id [String] The ID of the individual to be denied.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if from_id == to_id:
      return

    transaction = self.redis_connection.pipeline()
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), to_id)
    transaction.execute()

  def clear(self, id, scope = None):
    '''
    Clears all relationships (in either direction) stored for an individual.
    Helpful to prevent orphaned associations when deleting users.

    @param id [String] ID of the individual to clear info for.
    @param scope [String] Scope for the call.
    '''
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
    '''
    Check to see if one individual has blocked another individual.

    @param id [String] ID of the individual checking the blocked status.
    @param blocked_id [String] ID of the individual to see if they are blocked by id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, id), blocked_id) != None

  def is_blocked_by(self, id, blocked_by_id, scope = None):
    '''
    Check to see if one individual is blocked by another individual.

    @param id [String] ID of the individual checking the blocked by status.
    @param blocked_id [String] ID of the individual to see if they have blocked id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, id), blocked_by_id) != None

  def is_follower(self, id, follower_id, scope = None):
    '''
    Check to see if one individual is a follower of another individual.

    @param id [String] ID of the individual checking the follower status.
    @param following_id [String] ID of the individual to see if they are following id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, id), follower_id) != None

  def is_following(self, id, following_id, scope = None):
    '''
    Check to see if one individual is following another individual.

    @param id [String] ID of the individual checking the following status.
    @param following_id [String] ID of the individual to see if they are being followed by id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, id), following_id) != None

  def is_reciprocated(self, from_id, to_id, scope = None):
    '''
    Check to see if one individual has reciprocated in following another individual.

    @param from_id [String] ID of the individual checking the reciprocated relationship.
    @param to_id [String] ID of the individual to see if they are following from_id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.is_following(from_id, to_id, scope) and self.is_following(to_id, from_id, scope)

  def is_pending(self, from_id, to_id, scope = None):
    '''
    Check to see if one individual has a pending relationship in following another individual.

    @param from_id [String] ID of the individual checking the pending relationships.
    @param to_id [String] ID of the individual to see if they are pending a follow from from_id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), from_id) != None

  def is_pending_with(self, from_id, to_id, scope = None):
    '''
    Check to see if one individual has a pending relationship with another.

    @param from_id [String] ID of the individual checking the pending relationships.
    @param to_id [String] ID of the individual to see if they are pending an approval from from_id.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zscore('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, to_id), from_id) != None

  def following_count(self, id, scope = None):
    '''
    Count the number of individuals that someone is following.

    @param id [String] ID of the individual to retrieve following count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, id))

  def followers_count(self, id, scope = None):
    '''
    Count the number of individuals that are following someone.

    @param id [String] ID of the individual to retrieve followers count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, id))

  def blocked_count(self, id, scope = None):
    '''
    Count the number of individuals that someone has blocked.

    @param id [String] ID of the individual to retrieve blocked count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, id))

  def blocked_by_count(self, id, scope = None):
    '''
    Count the number of individuals blocking another.

    @param id [String] ID of the individual to retrieve blocked_by count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, id))

  def reciprocated_count(self, id, scope = None):
    '''
    Count the number of individuals that have reciprocated a following relationship.

    @param id [String] ID of the individual to retrieve reciprocated following count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, id))

  def pending_count(self, id, scope = None):
    '''
    Count the number of relationships pending for an individual.

    @param id [String] ID of the individual to retrieve pending count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, id))

  def pending_with_count(self, id, scope = None):
    '''
    Count the number of relationships an individual has pending with another.

    @param id [String] ID of the individual to retrieve pending count for.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    return self.redis_connection.zcard('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, id))

  def following(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of followed individuals for a given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of followed individuals.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, id), page_options)

  def followers(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of followers for a given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of followers.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, id), page_options)

  def blocked(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of blocked individuals for a given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of blocked individuals.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, id), page_options)

  def blocked_by(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of individuals who have blocked a given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of blocking individuals.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, id), page_options)

  def reciprocated(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of individuals that have reciprocated a follow for a given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of individuals that have reciprocated a follow.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, id), page_options)

  def pending(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of pending relationships for a given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of pending relationships.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, id), page_options)

  def pending_with(self, id, page_options = None, scope = None):
    '''
    Retrieve a page of individuals that are waiting to approve the given ID.

    @param id [String] ID of the individual.
    @param page_options [Hash] Options to be passed for retrieving a page of pending relationships.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_options == None:
      page_options = self.__default_paging_options()

    return self.__members('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, id), page_options)

  def following_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of following relationships for an individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, id), page_size)

  def followers_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of follower relationships for an individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, id), page_size)

  def blocked_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of blocked relationships for an individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_key'], scope, id), page_size)

  def blocked_by_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of blocked_by relationships for an individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['blocked_by_key'], scope, id), page_size)

  def reciprocated_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of reciprocated relationships for an individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, id), page_size)

  def pending_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of pending relationships for an individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, id), page_size)

  def pending_with_page_count(self, id, page_size = None, scope = None):
    '''
    Count the number of pages of individuals waiting to approve another individual.

    @param id [String] ID of the individual.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    return self.__total_pages('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, id), page_size)

  def all(self, id, type, scope = None):
    '''
    Retrieve all of the individuals for a given id, type (e.g. following) and scope

    @param id [String] ID of the individual.
    @param type [String] One of 'following', 'followers', 'reciprocated', 'blocked', 'blocked_by', 'pending', 'pending_with'.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    self.__validate_relationship_type(type)
    count = getattr(self, '%s_count' % type)(id, scope)
    if count > 0:
      return getattr(self, '%s' % type)(id, {'page_size': count, 'page': 1}, scope)
    else:
      return []

  def count(self, id, type, scope = None):
    '''
    Retrieve a count of all of a given type of relationship for the specified id.

    @param id [String] ID of the individual.
    @param type [String] One of 'following', 'followers', 'reciprocated', 'blocked', 'blocked_by', 'pending', 'pending_with'.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    self.__validate_relationship_type(type)
    return getattr(self, '%s_count' % type)(id, scope)

  def page_count(self, id, type, page_size = None, scope = None):
    '''
    Retrieve a page count of a given type of relationship for the specified id.

    @param id [String] ID of the individual.
    @param type [String] One of 'following', 'followers', 'reciprocated', 'blocked', 'blocked_by', 'pending', 'pending_with'.
    @param page_size [int] Page size (default: Amico.DEFAULTS['page_size']).
    @param scope [String] Scope for the call.
    '''
    if page_size == None:
      page_size = self.DEFAULTS['page_size']

    if scope == None:
      scope = self.options['default_scope_key']

    self.__validate_relationship_type(type)
    return getattr(self, '%s_page_count' % type)(id, page_size, scope)

  # private methods

  # Valid relationtionships that can be used in #all, #count, #page_count, etc...
  VALID_RELATIONSHIPS = ['following', 'followers', 'reciprocated', 'blocked', 'blocked_by', 'pending', 'pending_with']

  def __validate_relationship_type(self, type):
    '''
    Ensure that a relationship type is valid.

    @param type [String] One of 'following', 'followers', 'reciprocated', 'blocked', 'blocked_by', 'pending', 'pending_with'.
    @raise [StandardError] if the type is not included in VALID_RELATIONSHIPS
    '''
    if type not in self.VALID_RELATIONSHIPS:
      raise Exception('Invalid relationship type given %s' % type)

  def __clear_bidirectional_sets_for_id(self, id, source_set_key, related_set_key, scope = None):
    '''
    Removes references to an individual in sets that are named with other individual's keys.
    Assumes two set keys that are used together such as followers/following, blocked/blocked_by, etc...

    @param id [String] The ID of the individual to clear info for.
    @param source_set_key [String] The key identifying the souce set to iterate over.
    @param related_set_key [String] The key identifying the sets that the idividual needs to be removed from.
    @param scope [String] Scope for the call.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    related_ids = self.redis_connection.zrange('%s:%s:%s:%s' % (self.options['namespace'], source_set_key, scope, id), 0, -1)
    transaction = self.redis_connection.pipeline()
    for related_id in related_ids:
      self.redis_connection.zrem('%s:%s:%s:%s' % (self.options['namespace'], related_set_key, scope, related_id), id)
    transaction.execute()

    self.redis_connection.delete('%s:%s:%s:%s' % (self.options['namespace'], source_set_key, scope, id))

  def __add_following_followers_reciprocated(self, from_id, to_id, scope = None):
    '''
    Add the following, followers and check for a reciprocated relationship. To be used from the
    +follow+ and +accept+ methods.

    @param from_id [String] The ID of the individual establishing the follow relationship.
    @param to_id [String] The ID of the individual to be followed.
    '''
    if scope == None:
      scope = self.options['default_scope_key']

    transaction = self.redis_connection.pipeline()
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['following_key'], scope, from_id), int(time.time()), to_id)
    transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['followers_key'], scope, to_id), int(time.time()), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_key'], scope, to_id), int(time.time()), from_id)
    transaction.zrem('%s:%s:%s:%s' % (self.options['namespace'], self.options['pending_with_key'], scope, from_id), int(time.time()), to_id)
    transaction.execute()

    if self.is_reciprocated(from_id, to_id, scope):
      transaction = self.redis_connection.pipeline()
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, from_id), int(time.time()), to_id)
      transaction.zadd('%s:%s:%s:%s' % (self.options['namespace'], self.options['reciprocated_key'], scope, to_id), int(time.time()), from_id)
      transaction.execute()

  def __total_pages(self, key, page_size):
    '''
    Count the total number of pages for a given key in a Redis sorted set.

    @param key [String] Redis key.
    @param page_size [int] Page size from which to calculate total pages.
    @return total number of pages for a given key in a Redis sorted set.
    '''
    return int(math.ceil(self.redis_connection.zcard(key) / float(page_size)))

  def __default_paging_options(self):
    '''
    Default paging options.

    @return a hash of the default paging options.
    '''
    default_options = {
      'page_size': self.DEFAULTS['page_size'],
      'page': 1
    }

    return default_options

  def __members(self, key, options = None):
    '''
    Retrieve a page of items from a Redis sorted set without scores.

    @param key [String] Redis key.
    @param options [Hash] Default options for paging.
    @return a page of items from a Redis sorted set without scores.
    '''
    if options == None:
      options = self.__default_paging_options()

    if options['page'] < 1:
      options['page'] = 1

    total_pages = self.__total_pages(key, options['page_size'])
    if options['page'] > total_pages:
      options['page'] = total_pages

    index_for_redis = options['page'] - 1
    starting_offset = (index_for_redis * options['page_size'])

    if starting_offset < 0:
      starting_offset = 0

    ending_offset = (starting_offset + options['page_size']) - 1
    return self.redis_connection.zrevrange(key, starting_offset, ending_offset, withscores = False)