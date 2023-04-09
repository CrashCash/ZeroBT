# python3 setup.py sdist
# pip3 install https://github.com/CrashCash/ZeroBT/raw/master/dist/zerobt-1.0.tar.gz
#
from setuptools import setup
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
      install_requires=['PyBluez', 'pydbus']
)
