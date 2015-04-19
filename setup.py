from setuptools import setup

setup(name='bups',
      version='0.1',
      description='Back-up tool for directories in a local filesystem',
      author='Jarno Saarimäki',
      author_email='j.saarimaki@gmail.com',
      packages=['bups'],
      package_data = {'bups': ['*.conf']},
      entry_points = {'console_scripts': ['bups = bups.main:main']}
      )
