from setuptools import setup, find_packages
import subprocess
import re

DEFAULT_VERSION = "0.0.0"


# convert version from git tag to pypi style
# V0.1-3-g908f162 -> V0.1.post3
def convert_version(version):
    print("ori version: {}".format(version))

    pattern = re.compile(
        r"^[rvVR]*(?P<main>[0-9\.]+)(\-(?P<post>[0-9]+))?(\-.+)?$")
    ver = pattern.search(version)

    if not ver:
        print("invalid version! return default version {}".format(DEFAULT_VERSION))
        return DEFAULT_VERSION

    new_ver = ver.group('main')

    if ver.group('post'):
        new_ver += ".post{}".format(ver.group('post'))

    print("new version: {}".format(new_ver))
    return new_ver


try:
    version = subprocess.check_output(
            'git describe --tags', shell=True).rstrip().decode('utf-8')
except subprocess.CalledProcessError:
    version = DEFAULT_VERSION

version = convert_version(version)

setup(name='thermal_engine',
      version=version,
      description='',
      url='https://github.com/cy-arduino/python_thermal_engine',
      author='ChihYing_Lin',
      author_email='',
      license='LGPL',
      packages=find_packages(exclude=['tests', 'test_*']),
      zip_safe=False)
