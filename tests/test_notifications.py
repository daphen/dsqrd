import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import dsqrd as daemon


class NotificationTest(unittest.TestCase):
    def deliver(self, *, active=False, viewed="other", focus_during_download=False):
        app = object.__new__(daemon.DQS)
        app.my_id = "me"
        app.dms = []
        app.guilds = []
        app.chan_guild = {"chat": daemon.DM_WS}
        app.app_active = active
        app.active_ch = viewed
        app.dm_group_name = {}
        calls = []
        finished = threading.Event()
        app.notifier = SimpleNamespace(notify=lambda *args, **kwargs: calls.append(args))
        entered = threading.Event()
        release = threading.Event()

        def avatar(*_args):
            entered.set()
            if not release.wait(2):
                raise AssertionError("avatar was not released")
            return "avatar.png"

        real_thread = threading.Thread
        workers = []

        def thread(*args, **kwargs):
            target = kwargs.pop("target")

            def run():
                try:
                    target()
                finally:
                    finished.set()

            worker = real_thread(*args, target=run, **kwargs)
            workers.append(worker)
            return worker

        with mock.patch.object(daemon, "cached_avatar", avatar), mock.patch.object(daemon.threading, "Thread", thread):
            app.maybe_notify({"user_id": "sender", "username": "Sender", "content": "hello"}, "chat", daemon.DM_WS)
            if active and viewed == "chat":
                self.assertFalse(entered.is_set())
            else:
                self.assertTrue(entered.wait(2))
                if focus_during_download:
                    app.app_active = True
                    app.active_ch = "chat"
                release.set()
                self.assertTrue(finished.wait(2))
                for worker in workers:
                    worker.join(2)
        return calls

    def test_viewed_chat_stays_silent(self):
        self.assertEqual(self.deliver(active=True, viewed="chat"), [])

    def test_other_chat_notifies_while_app_is_active(self):
        self.assertEqual(len(self.deliver(active=True)), 1)

    def test_unfocused_chat_notifies(self):
        self.assertEqual(len(self.deliver(viewed="chat")), 1)

    def test_chat_opened_during_avatar_download_stays_silent(self):
        self.assertEqual(self.deliver(focus_during_download=True), [])


class DaemonStartupTest(unittest.TestCase):
    def test_duplicate_start_does_not_replace_socket(self):
        with tempfile.TemporaryDirectory(prefix="dsqrd-singleton-") as directory:
            runtime = Path(directory)
            path = runtime / "dsqrd.sock"
            env = dict(os.environ, HOME=directory, XDG_RUNTIME_DIR=directory,
                       DBUS_SESSION_BUS_ADDRESS="unix:path=" + directory + "/no-session-bus")
            with socket.socket(socket.AF_UNIX) as listener, open(str(path) + ".lock", "a") as lease:
                listener.bind(str(path))
                listener.listen()
                inode = path.stat().st_ino
                fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = subprocess.run([sys.executable, daemon.__file__], env=env,
                                        capture_output=True, text=True, timeout=3)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(path.stat().st_ino, inode)
                self.assertIn("already running", result.stdout)


if __name__ == "__main__":
    unittest.main()
