from setuptools import setup

setup(
    name='cvra-bootloader',
    version='1.0.1',
    description='Client for the CVRA CAN bootloader',
    author='Club Vaudois de Robotique Autonome',
    author_email='info@cvra.ch',
    url='https://github.com/cvra/can-bootloader',
    license='BSD',
    packages=['cvra_bootloader', 'can'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Embedded Systems',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        ],
    install_requires=[
        'msgpack-python',
        'pyserial',
        'progressbar2',
        ],
    entry_points={
        'console_scripts': [
            'bootloader_flash=cvra_bootloader.bootloader_flash:main',
            'bootloader_change_id=cvra_bootloader.change_id:main',
            'bootloader_read_config=cvra_bootloader.read_config:main',
            'bootloader_run_app=cvra_bootloader.run_application:main',
            'bootloader_write_config=cvra_bootloader.write_config:main',
            ],
        },
    )

