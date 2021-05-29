# python3 setup.py sdist
# pip install https://github.com/CrashCash/ZeroBT/raw/master/dist/zerobt-1.0.tar.gz
#
from distutils.core import setup
desc="""\
ZeroBT
======
A Python library to connect to a Zero electric motorcycle via Bluetooth and retrieve information.
"""

setup(name='zerobt',
      author='Gene Cash',
      author_email='genecash@fastmail.com',
      url='https://github.com/CrashCash/ZeroBT',
      version='1.0',
      py_modules=['zerobt'],
)
