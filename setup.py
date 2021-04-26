from distutils.core import setup


long_description = """python-btrfs is a Python 3 library that provides ways to interact
programmatically with an online btrfs file system.

It provides a pure python shadow implementation of data structures used in
btrfs together with convenient wrappers around the collection of kernel
functions that are available in the btrfs kernel API.

Using them, we can examine the secret inner world of a btrfs file system for
educational purposes.

The target audience for using the library is system administrators and
developers who want to discover more about the internals of a btrfs file
system, or want to create adjusted monitoring or administration tools that are
optimized for their specific use cases.

python-btrfs does not directly access disk storage, it only uses functions
available in the kernel interface, using system calls. This also means that
python-btrfs can not be used to repair a broken filesystem whenever the running
Linux kernel cannot properly mount it.
"""
long_description_content_type = 'text/markdown'


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
        'bin/btrfs-usage-report',
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
