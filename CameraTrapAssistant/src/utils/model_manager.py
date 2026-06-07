"""Validate the model files required by Camera Trap Assistant."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


LFS_POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1"


@dataclass(frozen=True)
class ModelRequirement:
    filename: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ModelProblem:
    filename: str
    reason: str


def get_models_directory() -> Path:
    """Return the model directory in both source and PyInstaller builds."""
    return Path(__file__).resolve().parent.parent / "models" / "weights"


def get_manifest_path() -> Path:
    """Return the model manifest in both source and PyInstaller builds."""
    return Path(__file__).resolve().parent.parent / "models" / "model_manifest.json"


def load_manifest(path: Path | None = None) -> tuple[ModelRequirement, ...]:
    manifest_path = path or get_manifest_path()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError(f"Unsupported model manifest: {manifest_path}")

    return tuple(
        ModelRequirement(
            filename=item["filename"],
            size=int(item["size"]),
            sha256=item["sha256"].lower(),
        )
        for item in data["models"]
    )


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as model_file:
        while chunk := model_file.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def is_lfs_pointer(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size > 1024:
        return False
    with path.open("rb") as model_file:
        return model_file.read(len(LFS_POINTER_PREFIX)) == LFS_POINTER_PREFIX


def validate_model_file(
    path: Path,
    requirement: ModelRequirement,
    verify_hash: bool = True,
) -> ModelProblem | None:
    if not path.is_file():
        return ModelProblem(requirement.filename, "file is missing")
    if is_lfs_pointer(path):
        return ModelProblem(
            requirement.filename,
            "file is a Git LFS pointer, not a usable model",
        )
    actual_size = path.stat().st_size
    if actual_size != requirement.size:
        return ModelProblem(
            requirement.filename,
            f"unexpected size ({actual_size} bytes, expected {requirement.size})",
        )
    if verify_hash and sha256_file(path) != requirement.sha256:
        return ModelProblem(requirement.filename, "SHA-256 checksum mismatch")
    return None


def validate_models(
    models_directory: Path | None = None,
    manifest_path: Path | None = None,
    verify_hashes: bool = True,
) -> list[ModelProblem]:
    directory = models_directory or get_models_directory()
    problems: list[ModelProblem] = []

    for requirement in load_manifest(manifest_path):
        path = directory / requirement.filename
        problem = validate_model_file(path, requirement, verify_hashes)
        if problem:
            problems.append(problem)

    return problems


def load_trusted_checkpoint(
    path: str | Path,
    map_location=None,
    manifest_path: Path | None = None,
):
    """Load a manifest-verified bundled checkpoint that requires pickle."""
    checkpoint_path = Path(path).resolve()
    requirements = {
        requirement.filename: requirement
        for requirement in load_manifest(manifest_path)
    }
    requirement = requirements.get(checkpoint_path.name)
    if requirement is None:
        raise ValueError(
            f"Checkpoint is not listed in the model manifest: {checkpoint_path.name}"
        )

    if manifest_path is None:
        expected_path = (get_models_directory() / requirement.filename).resolve()
        if checkpoint_path != expected_path:
            raise ValueError(
                f"Refusing to load a checkpoint outside the bundled model directory: "
                f"{checkpoint_path}"
            )

    problem = validate_model_file(checkpoint_path, requirement)
    if problem:
        raise RuntimeError(f"{problem.filename}: {problem.reason}")

    import torch

    # PyTorch 2.6+ defaults to weights_only=True. This legacy DeepFaune
    # checkpoint contains trusted metadata and has been hash-verified above.
    return torch.load(
        checkpoint_path,
        map_location=map_location,
        weights_only=False,
    )


def format_model_problems(problems: list[ModelProblem]) -> str:
    details = "\n".join(f"- {problem.filename}: {problem.reason}" for problem in problems)
    return (
        "Camera Trap Assistant cannot start because its AI model files are "
        f"incomplete or damaged:\n\n{details}\n\n"
        "Install the application again from the official GitHub Releases page:\n"
        "https://github.com/noebernigaud/CameraTrapAssistant/releases"
    )
