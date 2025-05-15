import tarfile
import zipfile
from pathlib import Path
from platform import machine, system
from stat import S_IXGRP, S_IXOTH, S_IXUSR
from subprocess import PIPE, Popen
from typing import Callable

import py7zr
import requests

SYSTEM_CACHE_DIR = {
    "linux": Path().home() / ".cache" / "cachebin",
    "darwin": Path().home() / "Library" / "Caches" / "cachebin",
    "windows": Path().home() / "AppData" / "Local" / "cachebin",
}


def download_file(url: str, directory_path: Path | str, force: bool = False) -> Path:
    """
    Downloads a file from the given URL and saves it to the specified directory.

    Args:
        url (str): The URL of the file to download.
        directory_path (Path): The directory where the file will be saved.

    Returns:
        Path of the downloaded file.
    """
    directory_path = Path(directory_path)  # Ensure directory_path is a Path object
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise an error for bad responses

    directory_path.mkdir(parents=True, exist_ok=True)

    filename = url.split("/")[-1]  # Extract the filename from the URL
    file_path = directory_path / filename

    if not file_path.exists() or force:
        print(f"Downloading {url} to {file_path}...")
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

    return file_path


def extract_archive(archive_path: Path | str, extract_path: Path | str) -> Path:  # noqa: PLR0912
    """
    Extracts a compressed archive to the specified directory.

    Args:
        archive_path (Path): The path to the archive file.
        extract_to (Path): The directory where the archive will be extracted.
    """
    archive_path = Path(archive_path)
    extract_path = Path(extract_path)
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive {archive_path} does not exist.")

    extract_path.mkdir(parents=True, exist_ok=True)

    archive: zipfile.ZipFile | tarfile.TarFile | py7zr.SevenZipFile
    if archive_path.name.endswith(("tar.gz", "tgz")):
        archive = tarfile.open(archive_path, "r:gz")
    elif archive_path.name.endswith("tar.bz2"):
        archive = tarfile.open(archive_path, "r:bz2")
    elif archive_path.name.endswith("tar.xz"):
        archive = tarfile.open(archive_path, "r:xz")
    elif archive_path.name.endswith("tar"):
        archive = tarfile.open(archive_path, "r:")
    elif archive_path.name.endswith("zip"):
        archive = zipfile.ZipFile(archive_path, "r")
    elif archive_path.name.endswith("7z"):
        archive = py7zr.SevenZipFile(archive_path, "r")
    else:
        raise RuntimeError(f"Unsupported archive format: {archive_path}")

    extracted_parent_directory = extract_path

    top_item: zipfile.ZipInfo | tarfile.TarInfo | py7zr.FileInfo
    if isinstance(archive, zipfile.ZipFile):
        top_item = archive.infolist()[0]
        if top_item.is_dir():
            extracted_parent_directory = extract_path / top_item.filename

    elif isinstance(archive, tarfile.TarFile):
        top_item = archive.getmembers()[0]
        if top_item.isdir():
            extracted_parent_directory = extract_path / top_item.name

    elif isinstance(archive, py7zr.SevenZipFile):
        top_item = archive.list()[0]
        if top_item.is_directory:
            extracted_parent_directory = extract_path / top_item.filename

    if not extracted_parent_directory.exists() or not any(extracted_parent_directory.iterdir()):
        print(f"Extracting {archive_path} to {extract_path}...")
        archive.extractall(path=extract_path)
    return extracted_parent_directory


def make_executable(file_path: str | Path) -> None:
    file_path = Path(file_path)
    current_permissions = file_path.stat().st_mode
    # Add the executable bit for the owner, group, and others
    file_path.chmod(current_permissions | S_IXUSR | S_IXGRP | S_IXOTH)


class BinaryVersion:
    def __init__(self, version: str, parent: "BinaryManager"):
        self.parent = parent
        self.version = version
        self.url = self.parent.url_pattern.format(
            version=self.version,
            platform=self.parent._platform_string,
            extension=self.parent._extension,
            package_name=self.parent.package_name,
        )
        self.archive_name = self.url.split("/")[-1]
        self.archive_path = download_file(self.url, self.parent._downloads_directory)
        self.binary_directory_path = (
            extract_archive(self.archive_path, self.parent._package_directory / self.version)
            / self.parent._extracted_bin_path
        )

    def call(self, command: str, *args: str) -> str:
        """
        Calls the binary with the specified command and arguments.

        Args:
            command (str): The command to execute.
            *args (str): Additional arguments for the command.

        Returns:
            str: The output of the command.
        """
        if self.parent._system == "windows":
            binary_path_exe = self.binary_directory_path / f"{command}.exe"
            binary_path_bat = self.binary_directory_path / f"{command}.bat"
            if binary_path_exe.exists():
                command = f"{command}.exe"
            elif binary_path_bat.exists():
                command = f"{command}.bat"
        binary_path = self.binary_directory_path / command
        if not binary_path.exists():
            raise FileNotFoundError(f"Binary {binary_path} does not exist.")

        make_executable(binary_path)

        creation_flag = (
            0x08000000 if self.parent._system == "windows" else 0
        )  # set creation flag to not open in new console on windows
        process = Popen([str(binary_path), *args], stdout=PIPE, stderr=PIPE, creationflags=creation_flag)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"Command failed with error: {stderr.decode('utf-8')}")
        return stdout.decode("utf-8")

    # TODO: def clear_cache(self) -> None:


class BinaryManager:
    def __init__(
        self,
        package_name: str,
        url_pattern: str,
        get_archive_extension: Callable[[str], str],  # returns archive extension based on system
        get_platform_string: Callable[[str, str], str] = lambda system,
        architecture: f"{system}-{architecture}",  # returns platform string used in url_pattern
        get_extracted_bin_path: Callable[[str, str], str] = lambda system,
        architecture: "bin",  # returns extracted bin path
        cache_directory: Path | str | None = None,
    ):
        self.package_name = package_name
        self.url_pattern = url_pattern
        self._system = system().lower()
        self._architecture = machine().lower()
        self._platform_string = get_platform_string(self._system, self._architecture)
        self._extension = get_archive_extension(self._system)
        self._extracted_bin_path = get_extracted_bin_path(self._system, self._architecture)

        self._cache_directory: Path
        if cache_directory is None:
            cache_directory = SYSTEM_CACHE_DIR.get(self._system)
            if cache_directory is None:
                raise ValueError(f"Unsupported system: {self._system}")
            self._cache_directory = cache_directory
        else:
            self._cache_directory = Path(cache_directory)
        self._downloads_directory = self._cache_directory / "downloads"
        self._archive_directory = self._cache_directory / self.package_name
        self._packages_directory = self._cache_directory / "packages"
        self._package_directory = self._packages_directory / self.package_name
        self._versions: dict[str, BinaryVersion] = {}

    def get_version(self, version: str) -> BinaryVersion:
        """
        Adds a version to the manager.

        Args:
            version (str): The version to add.

        Returns:
            BinaryVersion object for the added version.
        """
        if version not in self._versions:
            self._versions[version] = BinaryVersion(version, self)
        return self._versions[version]

    # TODO: def clear_cache(self) -> None:
