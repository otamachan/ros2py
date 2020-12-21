from setuptools import setup

setup(
    name="ros2py-init",
    version="0.1.0",
    description="enable ros2py automatic activation",
    author="Tamamki Nishino",
    author_email="otamachan@gmail.com",
    url="https://rospypi.github.io/simple2",
    packages=["ros2py_init"],
    entry_points={
        "console_scripts": ["ros2py-init = ros2py_init:main"],
    },
)
