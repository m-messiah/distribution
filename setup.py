from setuptools import setup
from os.path import join, dirname
from sys import version_info

__author__ = u"m_messiah"
__author_email__ = u"m.muzafarov@gmail.com"
__version__ = u'2.3'

setup(
    name='distributor',
    version=__version__,
    packages=['distributor'],
    include_package_data=True,
    url='https://github.com/m-messiah/distributor',
    license='MIT',
    author=__author__,
    author_email=__author_email__,
    description='Nginx, Haproxy configs and DNS analyzer.',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    scripts=["distributor-gen"],
    install_requires=[
        "jinja2",
        "pyparsing",
        "dnspython%s" % (3 if version_info[0] == 3 else ""),
        "requests"
    ],
    test_suite="tests",
    keywords='haproxy nginx bind nic.ru',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
