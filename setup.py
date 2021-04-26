from distutils.core import setup


with open('README.md') as f:
    long_description = f.read()


def get_version():
    version_dict = {}
    with open('btrfs/version.py') as fp:
        exec(fp.read(), version_dict)
    return version_dict['__version__']


version = get_version()

setup(
    name='btrfs',
    packages=['btrfs'],
    version=version,
    description='Python module to interact programmatically with an online btrfs file system',
    long_description=long_description,
    author='Hans van Kranenburg',
    author_email='hans@knorrie.org',
    url='https://github.com/knorrie/python-btrfs',
    download_url='https://github.com/knorrie/python-btrfs/tarball/v{}'.format(version),
    keywords=['btrfs', 'filesystem'],
    scripts=[
        'bin/btrfs-balance-least-used',
        'bin/btrfs-orphan-cleaner-progress',
        'bin/btrfs-search-metadata',
        'bin/btrfs-space-calculator',
        'bin/btrfs-usage-report'
    ],
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
