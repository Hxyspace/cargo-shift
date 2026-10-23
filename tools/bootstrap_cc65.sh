#!/usr/bin/env bash
# Prefer a complete existing installation; otherwise build a pinned local copy.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if command -v cl65 >/dev/null && command -v ca65 >/dev/null && command -v ld65 >/dev/null; then
    printf 'Using installed cc65: %s\n' "$(command -v cl65)"
    cl65 --version
    exit 0
fi
tool_dir="$project_dir/.tools/cc65"
tool_revision=555282497c3ecf8b313d87d5973093af19c35bd5
if [ ! -d "$tool_dir/.git" ]; then
    if [ -e "$tool_dir" ]; then
        printf 'Refusing to overwrite existing non-repository directory: %s\n' "$tool_dir" >&2
        exit 1
    fi
    mkdir -p "$project_dir/.tools"
    git clone --depth 1 --branch V2.19 https://github.com/cc65/cc65.git "$tool_dir"
fi
if [ "$(git -C "$tool_dir" rev-parse HEAD)" != "$tool_revision" ]; then
    printf 'Unexpected local cc65 revision; expected %s\n' "$tool_revision" >&2
    exit 1
fi
build_log="$project_dir/.tools/cc65-build.log"
printf 'Building cc65; log: %s\n' "$build_log"
if ! make -C "$tool_dir" -j"${JOBS:-4}" >"$build_log" 2>&1; then
    tail -n 60 "$build_log" >&2
    exit 1
fi
"$tool_dir/bin/cl65" --version
printf 'Local toolchain ready: %s\n' "$tool_dir"
