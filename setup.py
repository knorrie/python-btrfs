from distutils.core import setup


with open('README.pypi') as f:
    long_description = f.read()

setup(
    name='btrfs',
    packages=['btrfs'],
    version='5',
    description='Python module to inspect btrfs filesystems.',
    long_description=long_description,
    author='Hans van Kranenburg',
    author_email='hans.van.kranenburg@mendix.com',
    url='https://github.com/knorrie/python-btrfs',
    download_url='https://github.com/knorrie/python-btrfs/tarball/v5',
    keywords=['btrfs', 'filesystem'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Filesystems',
        'Topic :: System :: Systems Administration',
    ],
)
