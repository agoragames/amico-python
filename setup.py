import sys
from amico import Amico

try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup

requirements = [req.strip() for req in open('requirements.pip')]

setup(
  name = 'amico',
  version = Amico.VERSION,
  author = 'David Czarnecki',
  author_email = 'dczarnecki@agoragames.com',
  packages = ['amico'],
  install_requires = requirements,
  url = 'https://github.com/agoragames/amico-python',
  license = 'LICENSE.txt',
  description = 'Relationships (e.g. friendships) backed by Redis.',
  long_description = open('README.md').read(),
  keywords = ['python', 'redis', 'friendships'],
  classifiers = [
    'Development Status :: 5 - Production/Stable',
    'License :: OSI Approved :: MIT License',
    'Intended Audience :: Developers',
    'Operating System :: POSIX',
    'Topic :: Communications',
    'Topic :: System :: Distributed Computing',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: Software Development :: Libraries'
  ]
)
