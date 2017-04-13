from setuptools import setup

setup(
    name='energy_monitor',
    version='0.95',
    packages=['energy_monitor',
              'sunspec',
              'sunspec.core',
              'sunspec.core.modbus',
              'sunspec.core.test',
              'sunspec.core.test.fake'],
    url='github.com/boul/energy-monitor',
    license='Apache2',
    author='Roeland Kuipers',
    author_email='roeland@boul.nl',
    description='Monitors DSMR4 P1 Smart Meter and ABB VSN300 PV logger'
                ' and sends stats to e.g. pvoutput.org',
    scripts=['bin/energy-monitor'],
    install_requires=['PySerial'],
    package_data={'sunspec': ['models/smdx/*']}
)
