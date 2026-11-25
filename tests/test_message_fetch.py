import unittest
from unittest import mock

import dsqrd as daemon


def message(mid):
    return {
        "id": str(mid), "timestamp": "2026-11-22T10:00:00+00:00",
        "content": "test message", "user_id": "sender", "username": "Test",
        "mentions": [], "embeds": [], "stickers": [],
    }


class MessageFetchTest(unittest.TestCase):
    def setUp(self):
        self.app = object.__new__(daemon.DQS)
        self.app.discord = mock.Mock()
        self.app.gateway = mock.Mock()
        self.app.chan_guild = {}
        for name in ("_seed_participation_cutoff", "_note_latest", "learn_participant", "queue_gifv"):
            setattr(self.app, name, mock.Mock())
        self.app.users_payload = mock.Mock(return_value={})
        self.events = []
        self.app.write = lambda conn, event: self.events.append(event)
        self.sleep = mock.patch.object(daemon.time, "sleep").start()
        self.addCleanup(mock.patch.stopall)

    def request(self, kind):
        if kind == "recent":
            self.app.send_recent(None, "channel")
        else:
            self.app.send_history(None, "channel", "older-than")

    def test_transient_failure_retries_and_delivers_messages(self):
        for kind in ("recent", "history"):
            with self.subTest(kind=kind):
                self.events.clear()
                self.app.discord.get_messages.reset_mock()
                self.app.discord.get_messages.side_effect = [None, [message(2), message(1)]]
                self.request(kind)
                events = [e for e in self.events if e["type"] == kind]
                self.assertEqual(len(events), 1)
                self.assertEqual(len(events[0]["msgs"]), 2)
                self.assertLess(float(events[0]["msgs"][0]["ts"]), float(events[0]["msgs"][1]["ts"]))
                self.assertNotIn("toast", [e["type"] for e in self.events])
                before = None if kind == "recent" else "older-than"
                self.assertEqual(self.app.discord.get_messages.call_args_list, [
                    mock.call("channel", num=50, before=before),
                    mock.call("channel", num=50, before=before),
                ])
        self.assertEqual(self.sleep.call_args_list, [mock.call(0.5), mock.call(0.5)])

    def test_persistent_failure_emits_only_error_without_empty_reset_or_history(self):
        for kind in ("recent", "history"):
            with self.subTest(kind=kind):
                self.events.clear()
                self.app.discord.get_messages.reset_mock()
                self.app.discord.get_messages.side_effect = [None, None]
                self.request(kind)
                self.assertEqual(self.app.discord.get_messages.call_count, 2)
                self.assertEqual(self.events, [{
                    "type": "toast", "text": "Could not load messages. Please try again.",
                }])

    def test_real_empty_channel_is_not_a_failure(self):
        for kind in ("recent", "history"):
            with self.subTest(kind=kind):
                self.events.clear()
                self.app.discord.get_messages.reset_mock()
                self.app.discord.get_messages.side_effect = [[]]
                self.request(kind)
                expected = {"type": kind, "channel": "channel", "msgs": []}
                if kind == "recent":
                    expected.update(reset=True, final=True)
                self.assertEqual(self.events, [expected])
                self.app.discord.get_messages.assert_called_once()
        self.sleep.assert_not_called()

    def test_retry_can_succeed_with_a_genuinely_empty_channel(self):
        for kind in ("recent", "history"):
            with self.subTest(kind=kind):
                self.events.clear()
                self.app.discord.get_messages.side_effect = [None, []]
                self.request(kind)
                self.assertEqual(self.events[0]["type"], kind)
                self.assertEqual(self.events[0]["msgs"], [])
                self.assertEqual(len(self.events), 1)

    def test_successful_recent_still_streams_chronological_chunks(self):
        self.app.discord.get_messages.return_value = [message(i) for i in range(45, 0, -1)]
        self.app.send_recent(None, "channel")
        recent = [e for e in self.events if e["type"] == "recent"]
        self.assertEqual([len(e["msgs"]) for e in recent], [20, 20, 5])
        self.assertTrue(recent[0]["reset"])
        self.assertNotIn("reset", recent[1])
        self.assertNotIn("final", recent[0])
        self.assertTrue(recent[-1]["final"])
        self.assertEqual(self.events[-1]["type"], "users")
        self.app.discord.get_messages.assert_called_once()
        self.sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
