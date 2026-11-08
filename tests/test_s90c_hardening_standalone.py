"""Run with Python directly; no HA installation, network or TV required."""

import ast
import importlib.util
from pathlib import Path
import tempfile
import unittest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components/samsungtv_smart"
spec = importlib.util.spec_from_file_location("safe_art_path", COMPONENT / "safe_art_path.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PathTests(unittest.TestCase):
    def test_valid_ids(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            for identifier in ("MY_F001", "SAM-123", "MY:123.abc"):
                name, path = module.thumbnail_path(directory, identifier)
                self.assertEqual(Path(path).parent, Path(directory).resolve())
                self.assertEqual(name, identifier.replace(":", "_") + ".jpg")

    def test_rejects_traversal_and_invalid_values(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            for identifier in ("../escape", "MY/../../escape", "MY\\..\\escape",
                               "/tmp/escape", "C:\\escape", "", "..", None,
                               "x\x00.jpg", "x\n", "a" * 201):
                with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                    module.thumbnail_path(directory, identifier)

    def test_rejects_existing_symlink_escape(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            base = Path(directory) / "cache"
            base.mkdir()
            outside = Path(directory) / "outside.jpg"
            outside.write_bytes(b"unchanged")
            try:
                (base / "MY_F001.jpg").symlink_to(outside)
            except OSError:
                self.skipTest("Creating symlinks is not permitted on this host")
            with self.assertRaises(ValueError):
                module.thumbnail_path(str(base), "MY_F001")
            self.assertEqual(outside.read_bytes(), b"unchanged")


class FeatureGateTests(unittest.TestCase):
    def test_art_operations_exit_before_accessing_runtime_or_network(self):
        # Execute the actual methods with only the policy constant in scope.
        # Any attempted access to self/session/HA fails, rather than being mocked away.
        cases = [("api/art.py", "open", False),
                 ("api/art.py", "supported", False),
                 ("api/art.py", "_send_art_request", None),
                 ("media_player.py", "_ensure_frame_tv_check", False),
                 ("media_player.py", "async_art_identify", "error"),
                 ("art_identify.py", "async_identify_for_entry", "error")]
        for filename, method, expected in cases:
            with self.subTest(method=method):
                tree = ast.parse((COMPONENT / filename).read_text(encoding="utf-8"))
                fn = next(n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef) and n.name == method)
                scope = {"FRAME_FEATURES_ENABLED": False}
                compiled = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), fn], type_ignores=[])
                exec(compile(ast.fix_missing_locations(compiled), filename, "exec"), scope)
                # Supply None only for required arguments; guards must run first.
                required = len(fn.args.posonlyargs + fn.args.args) - len(fn.args.defaults)
                kwargs = {a.arg: None for a, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults) if default is None}
                coroutine = scope[method](*([None] * required), **kwargs)
                try:
                    with self.assertRaises(StopIteration) as stopped:
                        coroutine.send(None)
                    result = stopped.exception.value
                finally:
                    coroutine.close()
                if expected == "error":
                    self.assertIn("disabled", result["error"])
                else:
                    self.assertIs(result, expected)

    def test_startup_art_registrations_are_inside_disabled_gate(self):
        tree = ast.parse((COMPONENT / "__init__.py").read_text(encoding="utf-8"))
        setup = next(n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name == "async_setup")
        gates = [n for n in setup.body if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == "FRAME_FEATURES_ENABLED"]
        self.assertEqual(len(gates), 1)
        def calls(node):
            return [n for n in ast.walk(node) if isinstance(n, ast.Call) and
                    ((isinstance(n.func, ast.Name) and n.func.id in ("_register_gallery_card", "_register_bundled_card")) or
                     (isinstance(n.func, ast.Attribute) and n.func.attr == "register_view"))]
        self.assertEqual(len(calls(setup)), 4)
        self.assertEqual(len(calls(gates[0])), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)

