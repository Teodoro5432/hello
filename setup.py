from setuptools import setup, find_packages

setup(
    name='bufr-encoder',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=['eccodes', 'numpy', 'pandas'],
)
