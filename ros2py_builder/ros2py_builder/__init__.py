import pathlib
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass, field
from string import Template
from typing import Dict, List, Optional, Set

import catkin_pkg.packages
import dacite
import yaml

# foxy
ROS_DISTRO_INDEX_URL = (
    "https://raw.githubusercontent.com/ros/rosdistro/master/foxy/distribution.yaml"
)
PACKAGE_MAPPING = {
    "python3-catkin-pkg-modules": "catkin_pkg",
    "python3-empy": "empy",
    "python3-numpy": "numpy",
    "python3-lark-parser": "lark",
    "tracetools": "ros2-tracetools",
    "setuptools": "setuptools",
    "wheel": "wheel",
    "gmock_vendor": None,
    "gtest_vendor": None,
    "fastcdr": None,
    "rosidl_typesupport_connext_c": None,
    "rosidl_typesupport_connext_cpp": None,
    "rmw_connext_cpp": None,
    "rmw_cyclonedds_cpp": None,
}


@dataclass
class BuildOption:
    cmake_args: List[str] = field(default_factory=list)
    build_requires: List[str] = field(default_factory=list)
    install_requires: List[str] = field(default_factory=list)
    python: bool = False


@dataclass
class Repository:
    name: str
    url: str
    version: str
    path: Optional[str]
    excludes: List[str] = field(default_factory=list)
    build: Dict[str, BuildOption] = field(default_factory=dict)
    patch: Optional[str] = None


def get_all_ros_packages() -> List[str]:
    all_ros_packages = []
    with urllib.request.urlopen(ROS_DISTRO_INDEX_URL) as response:
        for name, repository in yaml.safe_load(response.read())["repositories"].items():
            if "release" in repository:
                all_ros_packages.extend(repository["release"].get("packages", [name]))
    return all_ros_packages


def convert_depends(depends: List[str], all_ros_packages: List[str]) -> List[str]:
    packages: Set[str] = set()
    for depend in depends:
        if depend in PACKAGE_MAPPING:
            mapped = PACKAGE_MAPPING[depend]
            if mapped is not None:
                packages.add(mapped)
        elif depend in all_ros_packages:
            packages.add(depend)
    return ['"' + p + '"' for p in packages]


def build_package(
    package_dir: pathlib.Path,
    ros_package: catkin_pkg.package.Package,
    build_option: BuildOption,
    dest_dir: pathlib.Path,
    temp_dir: pathlib.Path,
    all_ros_packages: List[str],
) -> None:
    if (package_dir / "CMakeLists.txt").exists():
        package_name = PACKAGE_MAPPING.get(ros_package.name, ros_package.name)
        assert package_name is not None
        package_build_dir = temp_dir / package_name
        if len(list(dest_dir.glob(f"{package_name}-*.tar.gz"))) == 0:
            package_build_dir.mkdir()
            pathlib.Path(package_build_dir / "src").symlink_to(
                package_dir.resolve(), target_is_directory=True
            )
            template_dir = pathlib.Path(__file__).parent
            template = Template((template_dir / "setup.py.in").read_text())
            (package_build_dir / "setup.py").write_text(
                template.substitute(
                    {
                        "package_name": package_name,
                        "version": ros_package.version,
                        "cmake_args": str(build_option.cmake_args),
                        "python": str(build_option.python),
                        "install_requires": ",\n".join(
                            convert_depends(
                                [
                                    d.name
                                    for d in ros_package.build_export_depends
                                    + ros_package.buildtool_export_depends
                                    + ros_package.exec_depends
                                ]
                                + build_option.install_requires,
                                all_ros_packages,
                            ),
                        ),
                    }
                )
            )
            template = Template((template_dir / "pyproject.toml.in").read_text())
            (package_build_dir / "pyproject.toml").write_text(
                template.substitute(
                    {
                        "build_requires": ", ".join(
                            convert_depends(
                                [
                                    d.name
                                    for d in ros_package.build_depends
                                    + ros_package.buildtool_depends
                                ]
                                + build_option.build_requires
                                + ["setuptools", "wheel"],
                                all_ros_packages,
                            ),
                        ),
                    }
                )
            )
            content = (template_dir / "MANIFEST.in").read_text()
            (package_build_dir / "MANIFEST.in").write_text(content)
        build_python_package(package_build_dir, dest_dir)
    elif (package_dir / "setup.py").exists():
        build_python_package(package_dir, dest_dir)


def build_python_package(package_dir: pathlib.Path, dest_dir: pathlib.Path) -> None:
    package_name = package_dir.name
    if len(list(dest_dir.glob(f"{package_name}-*.tar.gz"))) == 0:
        subprocess.check_call(
            [
                sys.executable,
                "-s",
                "setup.py",
                "sdist",
                "--dist-dir",
                dest_dir.resolve(),
            ],
            cwd=str(package_dir),
        )
    sdist = next(dest_dir.glob(f"{package_name}-*.tar.gz"))
    if len(list(dest_dir.glob(f"{package_name}-*.whl"))) == 0:
        subprocess.check_call(
            [
                sys.executable,
                "-s",
                "-m",
                "pip",
                "wheel",
                #            "-v",
                "--no-deps",
                "--find-links",
                dest_dir,
                "--wheel-dir",
                dest_dir,
                sdist,
            ],
        )


def build_repository(
    repository: Repository,
    dest_dir: pathlib.Path,
    temp_dir: pathlib.Path,
    all_ros_packages: List[str],
) -> None:
    if (dest_dir / repository.name).exists():
        return
    repository_root_dir = temp_dir / "repo"
    repository_root_dir.mkdir(exist_ok=True)
    repository_dir = repository_root_dir / repository.name
    if not repository_dir.exists():
        subprocess.check_call(
            [
                "git",
                "clone",
                repository.url,
                repository_dir,
                "--depth",
                "1",
                "-b",
                repository.version,
            ],
        )
        if repository.patch:
            p = subprocess.Popen(
                "patch -p1", shell=True, stdin=subprocess.PIPE, cwd=str(repository_dir)
            )
            assert p.stdin is not None
            p.stdin.write(pathlib.Path(repository.patch).read_text().encode("utf-8"))
            p.stdin.close()
        subprocess.check_call(
            [
                "git",
                "-C",
                repository_dir,
                "submodule",
                "update",
                "--init",
                "--recursive",
            ],
        )
    build_targets = []
    ros_packages = catkin_pkg.packages.find_packages(str(repository_dir))
    while ros_packages:
        found_ros_packages = []
        for ros_package_path, ros_package in ros_packages.items():
            if ros_package.name in repository.excludes:
                found_ros_packages.append(ros_package_path)
            else:
                depends = set(
                    [
                        d.name
                        for d in ros_package.build_depends
                        + ros_package.buildtool_depends
                        + ros_package.buildtool_export_depends
                    ]
                )
                independent = True
                for another_package in ros_packages.values():
                    if another_package.name in depends:
                        independent = False
                        break
                if independent:
                    found_ros_packages.append(ros_package_path)
                    build_targets.append((ros_package_path, ros_package))
        for ros_package_path in found_ros_packages:
            del ros_packages[ros_package_path]
    for ros_package_path, ros_package in build_targets:
        package_dir = repository_dir / ros_package_path
        build_option = repository.build.get(ros_package.name, BuildOption())
        build_package(
            package_dir, ros_package, build_option, dest_dir, temp_dir, all_ros_packages
        )
    (dest_dir / repository.name).write_text("")


def main() -> None:
    all_ros_packages = get_all_ros_packages()
    with open("packages.yaml") as f:
        repositories_data = yaml.safe_load(f)
    repositories = [
        dacite.from_dict(data_class=Repository, data=repository_data,)
        for repository_data in repositories_data["repositories"]
    ]
    temp = tempfile.mkdtemp(prefix="ros2py-build-")
    temp_dir = pathlib.Path(temp)
    dest_dir = pathlib.Path(".".join([str(v) for v in sys.version_info[0:3]]) + "-dist")
    try:
        for repository in repositories:
            build_repository(repository, dest_dir, temp_dir, all_ros_packages)
    finally:
        print(f"remove {temp}")
