"""Report the oldest macOS release that can run an application bundle.

Every Mach-O file records the macOS version it was built against. The bundle as
a whole can only run on the highest of those versions, which is the value that
belongs in LSMinimumSystemVersion. Getting this wrong is the classic macOS
packaging mistake: the build succeeds, it runs on the build machine, and it
refuses to launch for everybody on an older system.

The load commands are parsed directly instead of shelling out to otool once per
file, because a frozen Python application contains thousands of binaries.

Usage:
    python packaging/macos/check-deployment-target.py "dist/Camera Trap Assistant.app"
    python packaging/macos/check-deployment-target.py --maximum 11.0 <bundle>
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path


MACHO_MAGICS = {
    b"\xcf\xfa\xed\xfe": ("<", True),   # 64-bit little endian
    b"\xce\xfa\xed\xfe": ("<", False),  # 32-bit little endian
    b"\xfe\xed\xfa\xcf": (">", True),   # 64-bit big endian
    b"\xfe\xed\xfa\xce": (">", False),  # 32-bit big endian
}
FAT_MAGICS = {b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}

LC_VERSION_MIN_MACOSX = 0x24
LC_BUILD_VERSION = 0x32
PLATFORM_MACOS = 1


def decode_version(packed: int) -> tuple[int, int, int]:
    """Expand the X.Y.Z version packed into a 32-bit field."""
    return (packed >> 16, (packed >> 8) & 0xFF, packed & 0xFF)


def format_version(version: tuple[int, int, int]) -> str:
    major, minor, patch = version
    if patch:
        return f"{major}.{minor}.{patch}"
    return f"{major}.{minor}"


def parse_version(text: str) -> tuple[int, int, int]:
    parts = [int(part) for part in text.split(".")]
    parts += [0] * (3 - len(parts))
    return tuple(parts[:3])


def read_slice_minimum(data: bytes, offset: int) -> tuple[int, int, int] | None:
    """Return the macOS version required by one architecture slice."""
    magic = data[offset : offset + 4]
    if magic not in MACHO_MAGICS:
        return None
    endian, is_64 = MACHO_MAGICS[magic]

    header_size = 32 if is_64 else 28
    number_of_commands, = struct.unpack_from(f"{endian}I", data, offset + 16)

    cursor = offset + header_size
    for _ in range(number_of_commands):
        if cursor + 8 > len(data):
            return None
        command, command_size = struct.unpack_from(f"{endian}II", data, cursor)
        if command_size < 8:
            return None
        if command == LC_VERSION_MIN_MACOSX and cursor + 12 <= len(data):
            packed, = struct.unpack_from(f"{endian}I", data, cursor + 8)
            return decode_version(packed)
        if command == LC_BUILD_VERSION and cursor + 16 <= len(data):
            platform, minos = struct.unpack_from(f"{endian}II", data, cursor + 8)
            if platform == PLATFORM_MACOS:
                return decode_version(minos)
        cursor += command_size
    return None


def read_minimum(path: Path) -> tuple[int, int, int] | None:
    """Return the highest macOS version required by any slice of a Mach-O file."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if len(data) < 8:
        return None

    magic = data[:4]
    if magic in FAT_MAGICS:
        endian = ">" if magic == b"\xca\xfe\xba\xbe" else "<"
        count, = struct.unpack_from(f"{endian}I", data, 4)
        versions = []
        for index in range(count):
            entry = 8 + index * 20
            if entry + 20 > len(data):
                break
            offset, = struct.unpack_from(f"{endian}I", data, entry + 8)
            version = read_slice_minimum(data, offset)
            if version:
                versions.append(version)
        return max(versions) if versions else None

    if magic in MACHO_MAGICS:
        return read_slice_minimum(data, 0)
    return None


def scan(root: Path) -> dict[Path, tuple[int, int, int]]:
    requirements: dict[Path, tuple[int, int, int]] = {}
    targets = [root] if root.is_file() else sorted(root.rglob("*"))
    for path in targets:
        if path.is_symlink() or not path.is_file():
            continue
        version = read_minimum(path)
        if version:
            requirements[path] = version
    return requirements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="application bundle or Mach-O file")
    parser.add_argument(
        "--maximum",
        help="fail when the bundle requires a macOS release newer than this",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="list the binaries that set the requirement",
    )
    parser.add_argument(
        "--print-version",
        action="store_true",
        help="print only the required version, for use by build scripts",
    )
    arguments = parser.parse_args()

    if not arguments.bundle.exists():
        print(f"error: {arguments.bundle} does not exist", file=sys.stderr)
        return 2

    requirements = scan(arguments.bundle)
    if not requirements:
        print(f"error: no Mach-O binaries found in {arguments.bundle}", file=sys.stderr)
        return 2

    highest = max(requirements.values())
    responsible = sorted(
        path for path, version in requirements.items() if version == highest
    )

    if arguments.print_version:
        print(format_version(highest))
        return 0

    print(f"Scanned {len(requirements)} Mach-O binaries")
    print(f"Oldest supported macOS: {format_version(highest)}")
    if arguments.list:
        for path in responsible[:20]:
            print(f"  {path}")
        if len(responsible) > 20:
            print(f"  ... and {len(responsible) - 20} more")
    else:
        print(f"Set by {len(responsible)} binaries, for example {responsible[0].name}")

    if arguments.maximum:
        allowed = parse_version(arguments.maximum)
        if highest > allowed:
            print(
                f"error: the bundle requires macOS {format_version(highest)}, "
                f"which is newer than the declared minimum "
                f"{format_version(allowed)}.\n"
                "Rebuild with an interpreter and wheels that target the older "
                "release, or raise LSMinimumSystemVersion to match.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
