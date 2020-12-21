# ros2py

Python packages for ROS2.
Build Python packages including ROS2 binaries.
This will enable to create a ROS2 virtual environment easily.

Tested environment:

* Ubuntu 18.04 / Python3.[6-7]
* MacOS

# How to

## Build

Create build environment

```bash
python3 -m venv dev
. ./dev/bin/active
pip install ros2py_build
```

Build all ROS2 Python Packages

```bash
ros2py_build
```

## Test

Create a virtual environment

```bash
python3 -m venv venv
. ./venv/bin/active
pip install -f dist3.2.6 rclpy std_msgs
pip install ros2py_init
ros2py_init
deactivate  # once deactivate
. ./venv/bin/active
```


```bash
. ./venv/bin/active
git clone https://github.com/ros2/examples.git
python examples/rclpy/topics/minimal_publisher/examples_rclpy_minimal_publisher/publisher_member_function.py
```
