from distutils.core import setup


with open('README.md') as f:
    long_description = f.read()

setup(
    name='btrfs',
    packages=['btrfs'],
    version='11',
    description='Python module to inspect btrfs filesystems',
    long_description=long_description,
    author='Hans van Kranenburg',
    author_email='hans@knorrie.org',
    url='https://github.com/knorrie/python-btrfs',
    download_url='https://github.com/knorrie/python-btrfs/tarball/v11',
    keywords=['btrfs', 'filesystem'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Filesystems',
        'Topic :: System :: Systems Administration',
    ],
)
