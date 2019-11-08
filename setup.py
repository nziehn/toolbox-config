from os import path
import setuptools

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

dependencies = [
    'cachetools >= 3.0.0',
    'PyYAML >= 3.0',
    'boto3 >= 1.8.0'
]


setuptools.setup(
    name='toolbox-config',
    version='0.0.1',
    description='Tooling to manage project configs for production, staging, local, etc',
    # long_description=long_description,
    # long_description_content_type='text/markdown',
    url='http://github.com/nziehn/toolbox-config',
    author='Nils Ziehn',
    author_email='nziehn@gmail.com',
    license='MIT',
    packages=[
        package for package in setuptools.find_packages() if package.startswith('toolbox')
    ],
    namespace_packages=['toolbox'],
    install_requires=dependencies,
    zip_safe=False
)