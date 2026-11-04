#!/bin/sh
# Fetch Renode (open-source firmware emulation platform) from its canonical
# release page and unpack it into ./renode/. Prints the tarball SHA-256.
set -eu
cd "$(dirname "$0")"

if ! command -v mono >/dev/null 2>&1; then
    echo "WARNING: 'mono' not found on PATH. Renode's portable Linux build"
    echo "needs a Mono runtime; install it first (e.g. apt install mono-runtime)."
fi

API="https://api.github.com/repos/renode/renode/releases/latest"
URL="$(curl -fsSL "$API" | grep -o '"browser_download_url": *"[^"]*portable[^"]*"' | head -1 | cut -d'"' -f4)"
if [ -z "$URL" ]; then
    echo "Could not resolve a portable Renode asset from $API" >&2
    echo "Download manually from https://github.com/renode/renode/releases" >&2
    exit 1
fi
echo "Downloading: $URL"
curl -fSL -o renode-portable.tar.gz "$URL"
sha256sum renode-portable.tar.gz
mkdir -p renode
tar -xzf renode-portable.tar.gz -C renode --strip-components=1
ls renode/renode
echo "Renode installed under sim/hwsim-package/renode/"
echo "Bundled H7 platforms: "
find renode -iname '*stm32h7*' -name '*.repl' || true
