#  SPDX-License-Identifier: Apache-2.0
#  © 2023 ETH Zurich and other contributors, see AUTHORS.txt for details

"""
This module is used to generically initiate our APIs by downloading artifacts from the artifact repository (PolyBox). Its functions can be called either at
image build time or at startup time.
"""

import tarfile
from os import error, makedirs, path, remove
from pathlib import Path
from typing import Tuple

from httpx import get, stream, Response
from tqdm import tqdm


def stem_tar_filename(file_path: str) -> str:
    return Path(file_path).stem.split('.')[0]


def artifact_exists(file_path: str, is_tar: bool = False) -> bool:
    if is_tar:
        base_dir = path.dirname(file_path)
        tar_exists = path.isdir(Path(base_dir, stem_tar_filename(file_path)))
        file_exists = path.isfile(file_path)
        if file_exists:
            print("file already exists...")
        if tar_exists:
            print("tar file already exists...")
        return file_exists or tar_exists
    else:
        return path.isfile(file_path)


def download_artifact(artifact_url: str, file_path: str, polybox_auth: Tuple[str, str]) -> str:
    print("Downloading artifact {} to file_path {}".format(artifact_url, file_path))

    resp = get(url=artifact_url, follow_redirects=True, auth=polybox_auth)
    resp.raise_for_status()  # Raise http error if one occurred
    with open(file_path, 'wb') as file:
        file.write(resp.content)

    return file_path


def download_artifact_with_progress(artifact_url: str, file_path: str, polybox_auth: Tuple[str, str]) -> str:
    print(f"Downloading artifact {artifact_url} to {file_path}")

    with open(file_path, 'wb') as disk_file:
        response: Response
        with stream(url=artifact_url, method="GET", follow_redirects=True, auth=polybox_auth, timeout=None) as response:
            response.raise_for_status()
            total_bytes = int(response.headers["Content-Length"])
            if total_bytes > 10 ** 9:
                print(f"This could take a while, grab a ☕ ...")

            with tqdm(total=total_bytes, unit_scale=True, unit_divisor=1024, unit="B") as progress:
                num_bytes_downloaded = response.num_bytes_downloaded
                for chunk in response.iter_bytes():
                    disk_file.write(chunk)
                    progress.update(response.num_bytes_downloaded - num_bytes_downloaded)
                    num_bytes_downloaded = response.num_bytes_downloaded

    return file_path


def unpack_tar_file(tar_filepath: str, download_dir: str) -> str:
    print(f"unpacking {tar_filepath} to {download_dir} ...")

    def track_progress(members):
        for member in members:
            print(f"extracting {member.name} ...")
            yield member

    with tarfile.open(f'{tar_filepath}', 'r') as tarball:
        tarball.extractall(path=f'{download_dir}', members=track_progress(tarball))

    if path.exists(tar_filepath):
        remove(tar_filepath)

    return stem_tar_filename(tar_filepath)


def download_if_not_exists(artifact_url: str, download_dir: str, polybox_auth: Tuple[str, str], is_tar: bool = False) -> str:
    """ Download a file if not exists (currently only supported for files)

    Attributes
    ----------
    artifact_url: the artifact url "https://polybox.ethz.ch/remote.php/dav/files/mtc_polybox/<path-to-your-file>"

    download_dir: to this dir the file will be downloaded

    polybox_auth: tuple of (polybox_usr, polybox_pwd)

    is_tar: if tar is active a tar file will be downloaded and unpacked

    """
    # If path does not exist (vol not attached), create it
    if not path.exists(download_dir):
        makedirs(download_dir)

    # Expect dir, not file
    if path.isfile(download_dir):
        raise error("Expect download_dir to be a directory: {}".format(download_dir))

    file_name = artifact_url.split("/")[-1]
    file_path = path.join(download_dir, file_name)

    if is_tar:
        extracted_dir_name = file_path.split(".tar")[0]
        if artifact_exists(extracted_dir_name, is_tar=True):
            return extracted_dir_name

        else:
            download_artifact_with_progress(artifact_url, file_path, polybox_auth)
            unpack_tar_file(file_path, download_dir)
            return extracted_dir_name
    else:
        if artifact_exists(file_path):
            return file_path
        else:
            return download_artifact_with_progress(artifact_url, file_path, polybox_auth)
