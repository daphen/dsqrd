import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class MessageListScrollTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("qs"), "Quickshell is required for the QML scroll regression")
    def test_history_origin_and_bottom_pinning(self):
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix="dsqrd-scroll-") as tmp:
            root = Path(tmp)
            ui = root / "ui"
            ui.mkdir()
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            (root / "home").mkdir()
            shutil.copy(repo / "ui/MessageList.qml", ui / "MessageList.qml")
            shutil.copy(repo / "tests/qml/message-list-origin.qml", root / "shell.qml")
            (ui / "qmldir").write_text(
                "MessageList 1.0 MessageList.qml\nMessageDelegate 1.0 MessageDelegate.qml\n"
                "singleton Backend 1.0 Backend.qml\n"
            )
            (ui / "MessageDelegate.qml").write_text(
                'import QtQuick\nRectangle { width: ListView.view.width; '
                'height: model.rowHeight + (width < 500 ? 12 : 0); color: "#333333" }\n'
            )
            (ui / "Backend.qml").write_text("""pragma Singleton
import QtQuick
QtObject {
    property ListModel messages: ListModel {}
    property string currentChannel: "test"
    property bool loadingOlder: false
    property int requests: 0
    signal reflowList()
    signal reactionChanged()
    signal aboutToPrepend()
    signal prepended(int n)
    signal sentMessage()
    signal jumpToMessage(string ts)
    function requestOlder() { requests++ }
}
""")
            env = dict(os.environ)
            env.update(
                HOME=str(root / "home"), XDG_RUNTIME_DIR=str(runtime),
                XDG_CACHE_HOME=str(root / "cache"), QT_QPA_PLATFORM="offscreen",
                QML_IMPORT_PATH=str(repo / "ui/vendor"),
                QML2_IMPORT_PATH=str(repo / "ui/vendor"),
            )
            run = subprocess.run(
                ["qs", "-p", str(root)], env=env, capture_output=True, text=True, timeout=20,
            )
            output = run.stdout + run.stderr
            self.assertEqual(run.returncode, 0, output)
            self.assertNotIn("FAIL", output, output)
            self.assertNotIn("TypeError", output, output)
            self.assertIn("PASS origin-aware history", output, output)


if __name__ == "__main__":
    unittest.main()
