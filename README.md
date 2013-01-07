# amico

Relationships (e.g. friendships) backed by Redis. This is a port of the [amico gem](https://github.com/agoragames/amico).

## Installation

`pip install amico`

Make sure your redis server is running! Redis configuration is outside the scope of this README, but
check out the [Redis documentation](http://redis.io/documentation).

## Usage

Be sure to import the Amico library:

```python
from amico import Amico
```

Amico is configured with a number of defaults:

```python
>>> Amico.DEFAULTS
{'namespace': 'amico', 'pending_follow': False, 'reciprocated_key': 'reciprocated', 'followers_key': 'followers', 'pending_with_key': 'pending_with', 'following_key': 'following', 'page_size': 25, 'pending_key': 'pending', 'blocked_by_key': 'blocked_by', 'default_scope_key': 'default', 'blocked_key': 'blocked'}
```

The initializer for Amico takes two optional parameters:

* `options` : Dictionary of updated defaults
* `redis_connection` : Connection to Redis

```python
>>> amico = Amico(redis_connection = redis)
```

```python
>>> amico.follow(1, 11)
>>> amico.is_following(1, 11)
True
>>> amico.is_following(11, 1)
False
>>> amico.follow(11, 1)
>>> amico.is_following(11, 1)
True
>>> amico.following_count(1)
1
>>> amico.followers_count(1)
1
>>> amico.unfollow(11, 1)
>>> amico.following_count(11)
0
>>> amico.following_count(1)
1
>>> amico.is_follower(1, 11)
False
>>> amico.following(1)
['11']
>>> amico.block(1, 11)
>>> amico.is_following(11, 1)
False
>>> amico.is_blocked(1, 11)
True
>>> amico.is_blocked_by(11, 1)
True
>>> amico.unblock(1, 11)
>>> amico.is_blocked(1, 11)
False
>>> amico.is_blocked_by(11, 1)
False
>>> amico.follow(11, 1)
>>> amico.follow(1, 11)
>>> amico.is_reciprocated(1, 11)
True
>>> amico.reciprocated(1)
['11']
```

Use amico (with pending relationships for follow):

```python
>>> amico = Amico(options = {'pending_follow': True}, redis_connection = redis)
>>> amico.follow(1, 11)
>>> amico.follow(11, 1)
>>> amico.is_pending(1, 11)
True
>>> amico.is_pending_with(11, 1)
True
>>> amico.is_pending(11, 1)
True
>>> amico.is_pending_with(1, 11)
True
>>> amico.accept(1, 11)
>>> amico.is_pending(1, 11)
False
>>> amico.is_pending_with(11, 1)
False
>>> amico.is_pending(11, 1)
True
>>> amico.is_pending_with(1, 11)
True
>>> amico.is_following(1, 11)
True
>>> amico.is_following(11, 1)
False
>>> amico.is_follower(11, 1)
True
>>> amico.is_follower(1, 11)
False
>>> amico.accept(11, 1)
>>> amico.is_pending(1, 11)
False
>>> amico.is_pending_with(11, 1)
False
>>> amico.is_pending(11, 1)
False
>>> amico.is_pending_with(1, 11)
False
>>> amico.is_following(1, 11)
True
>>> amico.is_following(11, 1)
True
>>> amico.is_follower(11, 1)
True
>>> amico.is_follower(1, 11)
True
>>> amico.is_reciprocated(1, 11)
True
>>> amico.follow(1, 12)
>>> amico.is_following(1, 12)
False
>>> amico.is_pending(1, 12)
True
>>> amico.deny(1, 12)
>>> amico.is_following(1, 12)
False
>>> amico.is_pending(1, 12)
False
```

All of the calls support a `scope` parameter to allow you to scope the calls to express relationships for different types of things. For example:

```python
>>> amico = Amico(options = {'default_scope_key': 'user'}, redis_connection = redis)
>>> amico.follow(1, 11)
>>> amico.is_following(1, 11)
True
>>> amico.is_following(1, 11, scope = 'user')
True
>>> amico.following(1)
['11']
>>> amico.following(1, scope = 'user')
['11']
>>> amico.is_following(1, 11, scope = 'project')
False
>>> amico.follow(1, 11, scope = 'project')
>>> amico.is_following(1, 11, scope = 'project')
True
>>> amico.following(1, scope = 'project')
['11']
```

You can retrieve all of a particular type of relationship using the `all(id, type, scope)` call. For example:

```python
>>> amico.follow(1, 11)
>>> amico.follow(1, 12)
>>> amico.all(1, 'following')
['12', '11']
```

`type` can be one of 'following', 'followers', 'blocked', 'blocked_by', reciprocated', 'pending' and 'pending_with'. Use this with caution as there may potentially be a large number of items that could be returned from this call.

You can clear all relationships that have been set for an ID by calling `clear(id, scope)`. You may wish to do this if you allow records to be deleted and you wish to prevent orphaned IDs and inaccurate follower/following counts. Note that this clears *all* relationships in either direction - including blocked and pending. An example:

```python
>>> amico.follow(11, 1)
>>> amico.block(12, 1)
>>> amico.following(11)
['1']
>>> amico.blocked(12)
['1']
>>> amico.clear(1)
>>> amico.following(11)
[]
>>> amico.blocked(12)
[]
```

## FAQ?

### Why use Redis sorted sets and not Redis sets?

Based on the work I did in developing [leaderboard](https://github.com/agoragames/leaderboard),
leaderboards backed by Redis, I know I wanted to be able to page through the various relationships.
This does not seem to be possible given the current set of commands for Redis sets.

Also, by using the "score" in Redis sorted sets that is based on the time of when a relationship
is established, we can get our "recent friends". It is possible that the scoring function may be
user-defined in the future to allow for some specific ordering.

## Contributing to amico

* Check out the latest master to make sure the feature hasn't been implemented or the bug hasn't been fixed yet
* Check out the issue tracker to make sure someone already hasn't requested it and/or contributed it
* Fork the project
* Start a feature/bugfix branch
* Commit and push until you are happy with your contribution
* Make sure to add tests for it. This is important so I don't break it in a future version unintentionally.
* Please try not to mess with the version or history. If you want to have your own version, or is otherwise necessary, that is fine, but please isolate to its own commit so I can cherry-pick around it.

## Copyright

Copyright (c) 2013 David Czarnecki. See LICENSE.txt for further details.
