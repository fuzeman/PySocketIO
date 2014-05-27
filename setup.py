from setuptools import setup

setup(
    name='PySocketIO',
    version='1.0.0-beta',
    url='http://github.com/fuzeman/PySocketIO/',

    author='Dean Gardiner',
    author_email='me@dgardiner.net',

    description='Python implementation of socket.io',
    packages=['pysocketio'],
    platforms='any',

    install_requires=[
        'PyEmitter',
        'PyEngineIO',
        'PySocketIO-Adapter',
        'PySocketIO-Parser',

        'gevent',
        'gevent-websocket'
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python'
    ],
)
