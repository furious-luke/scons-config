import os
from setuptools import setup, find_packages

setup(
    name='scons-config',
    version='0.1',
    author='Luke Hodkinson',
    author_email='furious.luke@gmail.com',
    maintainer='Luke Hodkinson',
    maintainer_email='furious.luke@gmail.com',
    url='https://github.com/furious-luke/scons-config',
    description='Augmented configuration for SCons',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Framework :: SCons',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Build Tools',
    ],
    license='BSD',

    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['*.txt', '*.js', '*.html', '*.*']},
    install_requires=['setuptools'],
)
