#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

FROM continuumio/miniconda as test

# Install api requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy required source files
COPY mtc_api_utils ./mtc_api_utils

CMD [ "python", "-m", "unittest", "discover" ]
