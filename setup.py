from setuptools import setup
from os.path import join, dirname

setup(
    name='distributor',
    version='1.0',
    packages=['distributor'],
    include_package_data=True,
    url='https://github.com/m-messiah/distributor',
    license='MIT',
    author='m_messiah',
    author_email='m.muzafarov@gmail.com',
    description='Nginx, Haproxy configs and DNS anayzer.',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),
    scripts=["distributor-gen"],
    install_requires=["jinja2", "pyparsing", "dnspython", "requests"],
    keywords='haproxy nginx bind nic.ru',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        #'Programming Language :: Python :: 3',
        #'Programming Language :: Python :: 3.2',
        #'Programming Language :: Python :: 3.3',
        #'Programming Language :: Python :: 3.4',
        #'Programming Language :: Python :: 3.5',
    ],
)
