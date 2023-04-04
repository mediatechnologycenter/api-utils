#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

from distutils.core import setup



setup(
    name='mtc_api_utils',
    version='0.5.0',
    description='Commonly used MTC API utils',
    url='https://gitlab.ethz.ch/mtc/libraries/api-utils',
    author="Media Technology Center (ETH Zürich)",
    author_email='mtc@ethz.ch',
    package_data={
        "mtc_api_utils": ["py.typed"],
    },
    packages=[
        "mtc_api_utils",
        "mtc_api_utils.cli_wrappers",
        "mtc_api_utils.clients",
    ],
    install_requires=[
        "fastapi>=0.95.0",
        "python-multipart>=0.0.6",
        "uvicorn>=0.21.1",
        "gunicorn>=20.1.0",
        "debugpy>=1.6.6",
        "firebase_admin>=6.1.0",
        "slack-sdk>=3.20.2",
        "httpx>=0.23.1",
        "tqdm>=4.65.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ]
)
