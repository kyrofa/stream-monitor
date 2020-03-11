from setuptools import setup, find_packages

setup(
    name="stream-monitor",
    version="0.0.1",
    author="Kyle Fazzari",
    author_email="kyrofa@ubuntu.com",
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["stream-monitor=stream_monitor.monitor:main"]},
)
