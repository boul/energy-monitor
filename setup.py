from distutils.core import setup

setup(
    name='energy_monitor',
    version='0.7',
    packages=['energy_monitor'],
    url='github.com/boul/energy-monitor',
    license='Apache2',
    author='Roeland Kuipers',
    author_email='roeland@boul.nl',
    description='Monitors DSMR4 P1 Smart Meter and ABB VSN300 PV logger'
                ' and sends stats to e.g. pvoutput.org'
)
