#!/usr/bin/env bash
set -euo pipefail

mkdir -p /home/vscode/.codex /home/vscode/.codex-persist
chown -R vscode:vscode /home/vscode/.codex /home/vscode/.codex-persist

persist_codex_file() {
    local file="$1"
    local source="/home/vscode/.codex/$file"
    local target="/home/vscode/.codex-persist/$file"

    if [ -f "$source" ] && [ ! -e "$target" ]; then
        cp "$source" "$target"
    fi

    if [ ! -e "$target" ]; then
        if [ "$file" = "installation_id" ]; then
            tr -d '\n' < /proc/sys/kernel/random/uuid > "$target"
        else
            touch "$target"
        fi
    fi

    chown vscode:vscode "$target"
    ln -sf "$target" "$source"
    chown -h vscode:vscode "$source"
}

for file in auth.json config.toml installation_id; do
    persist_codex_file "$file"
done

if [ -S /run/host-services/ssh-auth.sock ]; then
    chgrp vscode /run/host-services/ssh-auth.sock
    chmod 660 /run/host-services/ssh-auth.sock
fi
