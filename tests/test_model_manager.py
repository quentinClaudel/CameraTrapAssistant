import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SRC_DIR = Path(__file__).resolve().parents[1] / "CameraTrapAssistant" / "src"
sys.path.insert(0, str(SRC_DIR))

from utils.model_manager import (
    is_lfs_pointer,
    load_trusted_checkpoint,
    validate_models,
)


class ModelManagerTests(unittest.TestCase):
    def write_manifest(self, directory: Path, content: bytes) -> Path:
        manifest = {
            "schema_version": 1,
            "models": [
                {
                    "filename": "model.pt",
                    "size": len(content),
                    "sha256": hashlib.sha256(content).hexdigest(),
                }
            ],
        }
        path = directory / "manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_valid_model(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            content = b"valid model content"
            (directory / "model.pt").write_bytes(content)
            manifest = self.write_manifest(directory, content)

            self.assertEqual(validate_models(directory, manifest), [])

    def test_missing_model(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            manifest = self.write_manifest(directory, b"missing")

            problems = validate_models(directory, manifest)

            self.assertEqual(problems[0].reason, "file is missing")

    def test_lfs_pointer_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            pointer = (
                b"version https://git-lfs.github.com/spec/v1\n"
                b"oid sha256:1234\nsize 999\n"
            )
            model = directory / "model.pt"
            model.write_bytes(pointer)
            manifest = self.write_manifest(directory, pointer)

            self.assertTrue(is_lfs_pointer(model))
            problems = validate_models(directory, manifest)
            self.assertIn("Git LFS pointer", problems[0].reason)

    def test_checksum_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            expected = b"expected"
            actual = b"modified"
            (directory / "model.pt").write_bytes(actual)
            manifest = self.write_manifest(directory, expected)
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["models"][0]["size"] = len(actual)
            manifest.write_text(json.dumps(data), encoding="utf-8")

            problems = validate_models(directory, manifest)

            self.assertEqual(problems[0].reason, "SHA-256 checksum mismatch")

    def test_trusted_checkpoint_uses_explicit_legacy_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            content = b"trusted checkpoint"
            model = directory / "model.pt"
            model.write_bytes(content)
            manifest = self.write_manifest(directory, content)

            with patch("torch.load", return_value={"state_dict": {}}) as torch_load:
                result = load_trusted_checkpoint(
                    model,
                    map_location="cpu",
                    manifest_path=manifest,
                )

            self.assertEqual(result, {"state_dict": {}})
            torch_load.assert_called_once_with(
                model.resolve(),
                map_location="cpu",
                weights_only=False,
            )

    def test_trusted_checkpoint_rejects_tampered_file_before_loading(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            model = directory / "model.pt"
            model.write_bytes(b"expected")
            manifest = self.write_manifest(directory, b"expected")
            model.write_bytes(b"modified")

            with patch("torch.load") as torch_load:
                with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                    load_trusted_checkpoint(model, manifest_path=manifest)

            torch_load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
