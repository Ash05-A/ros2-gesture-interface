from setuptools import setup

package_name = 'gesture_bridge'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
         ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='yashda',
    maintainer_email='yashda@todo.todo',
    description='Gesture to ROS2 bridge',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'gesture_bridge_node = gesture_bridge.gesture_bridge_node:main',
        ],
    },
)
