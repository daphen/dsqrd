import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import unittest


REPO = Path(__file__).resolve().parents[1]


def launcher(package):
    source = (REPO / "flake.nix").read_text()
    source = source.split('        text = \'\'\n', 1)[1].split("\n        '';", 1)[0]
    return source.replace("${daemon}", str(package)).replace("''${", "${")


class WindowReopenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="dsqrd-reopen-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.runtime = self.root / "runtime"
        self.runtime.mkdir(mode=0o700)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.home = self.root / "home"
        self.home.mkdir()
        shared = Path.home() / ".local/share/qml"
        if shared.exists():
            (self.home / ".local/share").mkdir(parents=True)
            (self.home / ".local/share/qml").symlink_to(shared)
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.bind(str(self.runtime / "dsqrd.sock"))
        self.sock.listen()
        self.addCleanup(self.sock.close)
        self.env = dict(os.environ, HOME=str(self.home), XDG_RUNTIME_DIR=str(self.runtime),
                        XDG_CONFIG_HOME=str(self.home / ".config"), XDG_CACHE_HOME=str(self.root / "cache"),
                        XDG_STATE_HOME=str(self.root / "state"), QT_QPA_PLATFORM="offscreen",
                        QML_IMPORT_PATH=str(REPO / "ui/vendor"), QML2_IMPORT_PATH=str(REPO / "ui/vendor"),
                        PATH=str(self.bin) + ":" + os.environ["PATH"])
        for name in ("DISPLAY", "WAYLAND_DISPLAY", "QS_CONFIG_PATH", "QS_CONFIG_NAME", "QS_MANIFEST"):
            self.env.pop(name, None)
        self.script("pgrep", f"#!/bin/sh\necho {os.getpid()}\n")
        self.command = self.root / "dsqrd-client"
        self.command.write_text("#!/bin/bash\nset -euo pipefail\n" + launcher(self.root))
        self.command.chmod(0o755)

    def script(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def test_launcher_requires_explicit_success_and_keeps_single_instance_fallback(self):
        calls = self.root / "calls"
        self.env["CALLS"] = str(calls)
        self.script("qs", '''#!/bin/sh
printf '%s\\n' "$*" >> "$CALLS"
if [ "$1" = ipc ]; then
    printf '%s\\n' "$REPLY"
    exit "$STATUS"
fi
''')
        for reply, status, expected in (("true", 0, 1), ("Target not found.", 0, 2), ("", 1, 2), ("false", 0, 2)):
            with self.subTest(reply=reply, status=status):
                calls.write_text("")
                run = subprocess.run([str(self.command)], env=dict(self.env, REPLY=reply, STATUS=str(status)),
                                     capture_output=True, text=True, timeout=10)
                self.assertEqual(run.returncode, 0, run.stderr)
                argv = calls.read_text().splitlines()
                self.assertEqual(len(argv), expected, argv)
                self.assertIn("call -- window openWindow", argv[0])
                if expected == 2:
                    self.assertTrue(argv[1].startswith("--no-duplicate -p "), argv)

    @unittest.skipUnless(shutil.which("qs"), "Quickshell required for native-window lifecycle test")
    def test_real_ui_reopens_same_process_after_native_close(self):
        ui = self.root / "share/dsqrd/ui"
        shutil.copytree(REPO / "ui", ui)
        source = (ui / "shell.qml").read_text()
        source = source.rstrip()[:-1] + '''
    IpcHandler {
        target: "fixture"
        function closeNative() { win.contentItem.Window.window.close() }
        function nativeVisible(): bool {
            return win.contentItem.Window.window !== null && win.contentItem.Window.window.visible
        }
    }
}
'''
        (ui / "shell.qml").chmod(0o600)
        (ui / "shell.qml").write_text(source)
        log = (self.root / "ui.log").open("w")
        self.addCleanup(log.close)
        process = subprocess.Popen([str(self.command)], env=self.env, stdout=log, stderr=log)
        self.addCleanup(self.stop, process)

        def call(target, method):
            return subprocess.run(["qs", "ipc", "-p", str(ui), "call", "--", target, method],
                                  env=self.env, capture_output=True, text=True, timeout=5)

        def visible():
            return call("fixture", "nativeVisible").stdout.strip() == "true"

        deadline = time.monotonic() + 20
        while not visible():
            self.assertIsNone(process.poll(), (self.root / "ui.log").read_text())
            self.assertLess(time.monotonic(), deadline, (self.root / "ui.log").read_text())
            time.sleep(0.05)
        for _ in range(3):
            self.assertEqual(call("fixture", "closeNative").returncode, 0)
            self.assertFalse(visible(), (self.root / "ui.log").read_text())
            self.assertIsNone(process.poll())
            reopened = subprocess.run([str(self.command)], env=self.env, capture_output=True, text=True, timeout=10)
            self.assertEqual(reopened.returncode, 0, reopened.stderr)
            self.assertTrue(visible(), (self.root / "ui.log").read_text())
            self.assertIsNone(process.poll())
        repeated = subprocess.run([str(self.command)], env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertTrue(visible())
        self.assertEqual(len(list((self.runtime / "quickshell/by-pid").iterdir())), 1)
        self.assertNotIn("TypeError", (self.root / "ui.log").read_text())

    @staticmethod
    def stop(process):
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()
