from setuptools import setup

setup(name='bups',
      version='0.1',
      description='Back-up tool for directories in a local filesystem',
      author='Jarno Saarimäki',
      author_email='j.saarimaki@gmail.com',
      packages=['bups'],
      test_suite='nose.collector',
      install_requires=[
          'pyyaml>=3.11'
      ],
      tests_require=[
          'nose>=1.3.7',
          'mock>=1.3.0',
          'nose-parameterized>=0.3.5'
          ],
      entry_points = {'console_scripts': ['bups = bups.main:main']}
      )
