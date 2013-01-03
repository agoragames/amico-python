import redis

class Amico(object):
  VERSION = '1.0.0'

  DEFAULTS = {
  }

  def __init__(self, default_options = DEFAULTS):
    self.options = Amico.DEFAULTS.copy()
    self.options.update(default_options)
