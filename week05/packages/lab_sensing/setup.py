import os
from glob import glob
from setuptools import setup

package_name = 'lab_sensing'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='student',
    maintainer_email='student@example.com',
    description='TC70045E Week 5 sensor-health monitor',
    license='MIT',
    entry_points={
        'console_scripts': [
            'sensor_monitor = lab_sensing.sensor_monitor:main',
        ],
    },
)
