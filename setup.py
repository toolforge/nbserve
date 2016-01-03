from setuptools import setup

setup(
    name='nbserver',
    version='0.1',
    description='Configurable way to serve IPytohn Notebook (ipynb) and static files',
    url='https://github.com/yuvipanda/nbserve',
    author='Yuvi Panda',
    author_email='yuvipanda@riseup.net',
    license='3 Clause BSD',
    packages=['nbserver', 'paws'],  # paws is temporary
)
