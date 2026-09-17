# dsqrd — keyboard-driven Discord for Wayland

`dsqrd` is a native-feeling Discord desktop client built with a Python daemon
and a Quickshell/QML interface. It is designed for fast keyboard navigation,
compact message browsing, desktop notifications, media handling, and optional
conversation summaries.

> [!WARNING] dsqrd is an unofficial client. It uses Discord's private gateway
> and REST APIs, which may change without notice and may be subject to Discord's
> terms. Expect occasional breakage.

## Features

- Guild channels and direct messages
- Live gateway updates and recent-message history
- Send, reply, edit, delete, and react to messages
- Upload files, paste images, and record voice notes
- Open or save images, videos, GIFs, and attachments
- Threads, mentions, profiles, presence, mute controls, and voice channels
- Actionable desktop notifications
- Optional conversation summaries and follow-up questions
- Vim-style navigation with an in-app keybinding reference
- QR-code authentication through the official Discord mobile app

Press `?` in the app to open the current keybinding reference. The help view is
generated from the real keymap, so it remains authoritative as bindings change.

## Architecture

```text
Discord gateway + REST API
            │
            ▼
  Python daemon (dsqrd.py)
            │  newline-delimited JSON over $XDG_RUNTIME_DIR/dsqrd.sock
            ▼
     Quickshell/QML UI
```

The daemon owns authentication, gateway state, REST requests, notifications,
uploads, media conversion, and the Unix socket. The QML process owns rendering,
keyboard interaction, and local UI state. Keeping those responsibilities
separate allows the daemon to remain connected if the interface is restarted.

Compositor-specific launch, focus, and placement policy is intentionally outside
this repository. The packaged client starts one daemon and one UI instance but
does not depend on a particular Wayland compositor.

## Requirements

The Nix package provides the application runtime, including Python libraries,
Quickshell, FFmpeg, ImageMagick, Secret Service tooling, `mpv`, and `imv`. A
Linux Wayland session and a working Secret Service implementation are still
required.

The main Python dependencies are:

- `websocket-client`
- `pysocks`
- `filetype`
- `protobuf`
- `jeepney`
- `pycryptodome`
- `qrcode`
- `pillow`

## Run with Nix

Run the current checkout:

```sh
git clone https://github.com/daphen/dsqrd.git
cd dsqrd
nix run .
```

Build without launching:

```sh
nix build .#dsqrd
nix build .#dsqrd-client
```

The default package is `dsqrd-client`, which:

1. Starts the daemon if it is not already healthy.
1. Waits for `$XDG_RUNTIME_DIR/dsqrd.sock`.
1. Reuses an existing UI instead of launching a duplicate.
1. Starts the packaged Quickshell interface when needed.

For source-only daemon development, `./run-dsqrd.sh` enters the legacy
`shell.nix` environment and runs `dsqrd.py`. The flake remains the complete and
preferred runtime.

## Authentication

On first launch, dsqrd displays a QR code. Scan it with the official Discord
mobile app and approve the login there. The daemon stores the resulting session
in Secret Service; credentials are never exposed to QML.

An existing endcord-compatible `~/.config/dsqrd/profiles.json` is accepted as a
compatibility fallback, but QR authentication with Secret Service storage is the
supported path.

## Data and configuration

| Path                            | Purpose                                                  |
| ------------------------------- | -------------------------------------------------------- |
| `$XDG_RUNTIME_DIR/dsqrd.sock`   | Daemon-to-UI socket                                      |
| `~/.local/share/dsqrd/`         | Writable application data and preferences                |
| `~/.cache/dsqrd/`               | Avatars, previews, and temporary viewed media            |
| `~/.config/dsqrd/profiles.json` | Compatibility profile and optional summary configuration |
| `/tmp/dsqrd.log`                | Daemon output when started by the packaged launcher      |

Viewed media is cached under `~/.cache/dsqrd/view`; use the explicit save action
for files that should be kept.

## Optional integrations

### Conversation summaries

The catch-up menu can use an installed command-line provider or a configured API
provider. The first use opens an in-app setup flow and stores its choice in the
`summarize` block of `~/.config/dsqrd/profiles.json`.

### Custom message actions

Set `DSQRD_MESSAGE_ACTION` to expose an additional action for the selected
message. See [`docs/custom-message-actions.md`](docs/custom-message-actions.md)
for the versioned JSON payload contract.

## Development

Useful checks before submitting a change:

```sh
python -m py_compile dsqrd.py
nix build .#dsqrd
nix build .#dsqrd-client
```

The application code is organized as:

- `dsqrd.py` — daemon, socket protocol, Discord operations, and media handling
- `dchat/` — gateway, authentication, token storage, and protocol helpers
- `ui/` — the packaged Quickshell interface
- `flake.nix` — reproducible daemon and client packages
- `tests/` — focused authentication tests

## License and attribution

The Discord protocol layer began from endcord's `dchat` implementation and has
since been adapted for dsqrd's daemon and UI protocol. Check dependency sources
and file headers for their applicable licenses.
