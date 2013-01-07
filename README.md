# amico

Relationships (e.g. friendships) backed by Redis. This is a port of the [amico gem](https://github.com/agoragames/amico).

## Installation

`pip install amico`

Make sure your redis server is running! Redis configuration is outside the scope of this README, but
check out the [Redis documentation](http://redis.io/documentation).

## Usage

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
