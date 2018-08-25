import os
import subprocess
import sys

import setuptools.command.build_py


THIS_DIR = os.path.dirname(__file__)


def build_nng_lib():
    # cannot import build_pynng at the top level becuase cffi may not be
    # installed yet (since it is a dependency, and this script installs
    # dependencies).  Bootstrapping!
    import build_pynng
    if os.path.exists(build_pynng.objects[0]):
        # the object file we were planning on building already exists; we'll
        # just use it!
        return
    if sys.platform == 'win32':
        # pick the correct cmake generator, based on the Python version.
        # from https://wiki.python.org/moin/WindowsCompilers for Python
        # version, and cmake --help for list of CMake generator names
        major, minor, *_ = sys.version_info
        cmake_generators = {
            (3, 0): 'Visual Studio 9 2008',
            (3, 1): 'Visual Studio 9 2008',
            (3, 2): 'Visual Studio 9 2008',
            (3, 3): 'Visual Studio 10 2010',
            (3, 4): 'Visual Studio 10 2010',
            (3, 5): 'Visual Studio 14 2015',
            (3, 6): 'Visual Studio 14 2015',
        }
        gen = cmake_generators[(major, minor)]

        is_64bit = sys.maxsize > 2**32
        if is_64bit:
            gen += ' Win64'

        cmd = [os.path.join(THIS_DIR, 'build_nng.bat'), gen]

    else:
        script = os.path.join(THIS_DIR, 'build_nng.sh')
        cmd = ['/bin/bash', script]

    subprocess.check_call(cmd)


# TODO: this is basically a hack to get something to run before running cffi
# extnsion builder. subclassing something else would be better!
class BuildCommand(setuptools.command.build_py.build_py):
    """Custom build command."""

    def run(self):
        build_nng_lib()
        super(BuildCommand, self).run()


with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setuptools.setup(
    cmdclass={
        'build_py': BuildCommand,
    },
    name='pynng',
    version='0.1.0-pre',
    author='Cody Piersall',
    author_email='cody.piersall@gmail.com',
    description='Networking made simply using nng',
    long_description=long_description,
    license='MIT',
    keywords='networking nng nanomsg zmq messaging message',
    long_description_content_type='text/markdown',
    url='https://github.com/codypiersall/pynng',
    packages=setuptools.find_packages(),
    classifiers=(
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Topic :: Software Development :: Libraries',
        'Topic :: System :: Networking',
    ),
    setup_requires=['cffi'],
    cffi_modules=['build_pynng.py:ffibuilder'],
)

