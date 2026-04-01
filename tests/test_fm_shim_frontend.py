import importlib.machinery
import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


class _DummySignal:
    def connect(self, *_args, **_kwargs):
        return None


class _DummyObject:
    def __init__(self, *_args, **_kwargs):
        pass

    def __call__(self, *_args, **_kwargs):
        return self

    def __getattr__(self, _name):
        return self

    def __or__(self, _other):
        return 0

    def connect(self, *_args, **_kwargs):
        return None

    def installEventFilter(self, *_args, **_kwargs):
        return None


def _load_module():
    qtcore = types.ModuleType("PyQt5.QtCore")
    qtcore.QTimer = _DummyObject
    qtcore.QObject = _DummyObject

    class _DummyQEvent:
        Type = types.SimpleNamespace(Show=1, Hide=2)

    qtcore.QEvent = _DummyQEvent

    qtgui = types.ModuleType("PyQt5.QtGui")
    qtgui.QFontDatabase = types.SimpleNamespace(
        SystemFont=types.SimpleNamespace(FixedFont=0),
        systemFont=lambda *_args, **_kwargs: None,
    )

    qtwidgets = types.ModuleType("PyQt5.QtWidgets")
    for name in [
        "QApplication", "QDialog", "QLabel", "QTextEdit", "QPushButton",
        "QVBoxLayout", "QHBoxLayout", "QWidget", "QScrollBar", "QLayout",
        "QMessageBox",
    ]:
        setattr(qtwidgets, name, _DummyObject)

    pyqt5 = types.ModuleType("PyQt5")
    sys.modules.setdefault("PyQt5", pyqt5)
    sys.modules["PyQt5.QtCore"] = qtcore
    sys.modules["PyQt5.QtGui"] = qtgui
    sys.modules["PyQt5.QtWidgets"] = qtwidgets

    module_path = Path(
        "/workspace/security-misc/usr/lib/python3/dist-packages/"
        "fm_shim_frontend/fm_shim_frontend.py#security-misc-shared"
    )
    loader = importlib.machinery.SourceFileLoader(
        "fm_shim_frontend_test", str(module_path)
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


MODULE = _load_module()


class FmShimFrontendTests(unittest.TestCase):
    def test_decode_ascii_path_rejects_percent_encoded_unicode(self):
        self.assertIsNone(
            MODULE.decode_ascii_path_from_uri_path("/tmp/%E2%80%AEevil")
        )

    def test_decode_ascii_path_rejects_invalid_utf8_bytes(self):
        self.assertIsNone(MODULE.decode_ascii_path_from_uri_path("/tmp/%FF"))

    def test_get_path_list_accepts_printable_ascii_path(self):
        with tempfile.TemporaryDirectory(prefix="fm shim ") as tmpdir:
            uri = Path(tmpdir).as_uri()
            path_list = MODULE.get_path_list_from_uris("--show-folders", [uri])
            self.assertEqual(path_list, [Path(tmpdir).resolve()])

    def test_get_path_list_rejects_percent_encoded_unicode_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            uri = Path(tmpdir).as_uri() + "%E2%80%AE"
            self.assertEqual(
                MODULE.get_path_list_from_uris("--show-folders", [uri]), []
            )


if __name__ == "__main__":
    unittest.main()
