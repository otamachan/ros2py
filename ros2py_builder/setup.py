from setuptools import setup

setup(
    name="ros2py-builder",
    version="0.1.0",
    packages=["ros2py_builder"],
    package_data={"ros2py_builder": ["*.in"]},
    description="ros2py package build tool",
    author="Tamamki Nishino",
    author_email="otamachan@gmail.com",
    url="https://rospypi.github.io/simple2",
    install_requires=[
        "catkin_pkg",
        "dacite",
        "pyyaml",
        "dataclasses; python_version<'3.7'",
    ],
    entry_points={
        "console_scripts": [
            "ros2py-build = ros2py_builder:main",
        ],
    },
)
