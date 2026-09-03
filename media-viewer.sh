#!/usr/bin/env bash
set -e

ctl="$(command -v mediactl || true)"
profile_ctl="/etc/profiles/per-user/${USER:-${LOGNAME:-daphen}}/bin/mediactl"
if [[ -n "$ctl" ]]; then
    exec "$ctl" view "$@"
elif [[ -x "$profile_ctl" ]]; then
    exec "$profile_ctl" view "$@"
fi

target=$1
type=${2:-img}
mapfile -t files <<< "$target"

case "$type" in
    img|gif)
        exec setsid -f imv "${files[@]}"
        ;;
    video|mix)
        exec setsid -f mpv --loop --no-terminal "${files[@]}"
        ;;
    audio)
        exec setsid -f mpv --no-terminal --force-window=immediate --keep-open=yes --loop-file=no "${files[@]}"
        ;;
    *)
        exec xdg-open "$target"
        ;;
esac
