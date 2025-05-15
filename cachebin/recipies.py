from .cachebin import BinaryManager


def process_map(map: dict[str, str], key_description: str, key: str) -> str:
    result = map.get(key)
    if result is None:
        raise ValueError(f"Unsupported {key_description}: {key}")
    return result


pandoc_manager = BinaryManager(
    package_name="pandoc",
    url_pattern="https://github.com/jgm/{package_name}/releases/download/{version}/{package_name}-{version}-{platform}.{extension}",
    get_platform_string=lambda system, architecture: process_map(
        {
            "darwin-x86_64": "x86_64-macOS",
            "darwin-arm64": "arm64-macOS",
            "linux-x86_64": "linux-amd64",
            "linux-aarch64": "linux-arm64",
            "windows-amd64": "windows-x86_64",
        },
        "platform",
        f"{system}-{architecture}",
    ),
    get_archive_extension=lambda system: "tar.gz" if system == "linux" else "zip",
)

tinytex_manager = BinaryManager(
    package_name="tinytex",
    url_pattern="https://github.com/rstudio/tinytex-releases/releases/download/{version}/TinyTeX-1-{version}.{extension}",
    get_archive_extension=lambda system: process_map(
        {"windows": "zip", "linux": "tar.gz", "darwin": "tgz"}, "system", system
    ),
    get_extracted_bin_path=lambda system, architecture: f"bin/universal-{system}"
    if system == "darwin"
    else f"bin/{system}"
    if system == "windows"
    else f"bin/{architecture}-{system}",
)

pandoc_crossref_manager = BinaryManager(
    package_name="pandoc-crossref",
    url_pattern="https://github.com/lierdakil/{package_name}/releases/download/{version}/{package_name}-{platform}.{extension}",
    get_platform_string=lambda system, architecture: process_map(
        {
            "darwin-x86_64": "macOS-X64",
            "darwin-arm64": "macOS-ARM64",
            "linux-x86_64": "Linux-X64",
            "windows-amd64": "Windows-X64",
        },
        "platform",
        f"{system}-{architecture}",
    ),
    get_archive_extension=lambda system: "7z" if system == "windows" else "tar.xz",
    get_extracted_bin_path=lambda system, architecture: "",
)
