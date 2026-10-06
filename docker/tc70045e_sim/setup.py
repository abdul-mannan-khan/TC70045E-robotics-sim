from glob import glob
from setuptools import setup

package_name = 'tc70045e_sim'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/urdf', glob('urdf/*')),
        ('share/' + package_name + '/worlds', glob('worlds/*')),
        ('share/' + package_name + '/config', glob('config/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Abdul Manan Khan',
    maintainer_email='khanabd@uwl.ac.uk',
    description='TC70045E simulated lab robot and virtual lab instruments',
    license='MIT',
    entry_points={
        'console_scripts': [
            'wheel_odometry = tc70045e_sim.wheel_odometry:main',
            'magnetometer = tc70045e_sim.magnetometer:main',
            'stereo_depth = tc70045e_sim.stereo_depth:main',
            'battery = tc70045e_sim.battery:main',
            'motor_bench = tc70045e_sim.motor_bench:main',
            'virtual_mcu = tc70045e_sim.virtual_mcu:main',
            'imu_noise_model = tc70045e_sim.imu_noise_model:main',
        ],
    },
)
