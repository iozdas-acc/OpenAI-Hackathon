#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DIR="$ROOT_DIR/skills"
TARGET_DIR="${CODEX_HOME:-$HOME/.codex}/skills"

mkdir -p "$TARGET_DIR"

link_skill() {
  local source_dir="$1"
  local skill_name
  skill_name="$(basename "$source_dir")"
  local target="$TARGET_DIR/$skill_name"

  if [[ -L "$target" ]]; then
    local current
    current="$(readlink "$target")"
    if [[ "$current" == "$source_dir" ]]; then
      echo "ok    $skill_name"
      return
    fi
    echo "skip  $skill_name (existing symlink to $current)"
    return
  fi

  if [[ -e "$target" ]]; then
    echo "skip  $skill_name (target exists at $target)"
    return
  fi

  ln -s "$source_dir" "$target"
  echo "link  $skill_name"
}

while IFS= read -r -d '' skill_file; do
  link_skill "$(dirname "$skill_file")"
done < <(find "$SKILLS_DIR" -name SKILL.md -print0 | sort -z)

echo
echo "Skills synced into $TARGET_DIR"
echo "Restart Codex to pick up new skills."
