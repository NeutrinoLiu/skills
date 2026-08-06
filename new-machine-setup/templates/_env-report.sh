#!/usr/bin/env bash
# Sourced by every generated script. Prints the consolidated environment this
# setup owns — what is in the rc files, and whether it is live in the shell you
# are standing in right now.
#
# Not meant to be executed directly.

MARK_START='# >>> new-machine-setup >>>'
MARK_END='# <<< new-machine-setup <<<'

# Rewrite the marked block in an rc file. Idempotent: the old block is deleted
# before the new one is appended, so re-runs never stack duplicates.
# Usage: env_block_write <rcfile> 'VAR=value' ['VAR2=value2' ...]
env_block_write() {
  local rc="$1"; shift
  [ -f "$rc" ] || return 0
  sed -i "\|$MARK_START|,\|$MARK_END|d" "$rc"
  {
    printf '\n%s\n' "$MARK_START"
    local kv
    for kv in "$@"; do
      printf 'export %s="%s"\n' "${kv%%=*}" "${kv#*=}"
    done
    printf '%s\n' "$MARK_END"
  } >> "$rc"
}

# Print every variable this setup manages, where it is written, whether it is
# live in the current shell, and whether the path it names exists.
env_report() {
  local rcs=("$HOME/.bashrc" "$HOME/.zshrc")
  local names=() rc line name val

  for rc in "${rcs[@]}"; do
    [ -f "$rc" ] || continue
    while IFS= read -r line; do
      case "$line" in
        export\ *=*)
          name="${line#export }"; name="${name%%=*}"
          case " ${names[*]-} " in *" $name "*) ;; *) names+=("$name") ;; esac
          ;;
      esac
    done < <(sed -n "\|$MARK_START|,\|$MARK_END|p" "$rc")
  done

  printf '\n\033[1mEnvironment managed by this setup\033[0m\n'

  if [ ${#names[@]} -eq 0 ]; then
    printf '  \033[90m(nothing yet — 2-shell-and-conda.sh writes the first block)\033[0m\n\n'
    return 0
  fi

  # One block per variable rather than a table: paths are long and unbounded,
  # and a column layout silently mangles them.
  for name in "${names[@]}"; do
    local where="" first_val="" conflict=0 seen=0
    for rc in "${rcs[@]}"; do
      [ -f "$rc" ] || continue
      line=$(sed -n "\|$MARK_START|,\|$MARK_END|p" "$rc" | grep "^export $name=" || true)
      [ -n "$line" ] || continue
      val="${line#*=}"; val="${val%\"}"; val="${val#\"}"
      where="${where:+$where, }$(basename "$rc")=$val"
      if [ "$seen" -eq 0 ]; then first_val="$val"; seen=1
      elif [ "$val" != "$first_val" ]; then conflict=1
      fi
    done
    val="$first_val"

    printf '\n  \033[1m%s\033[0m = %s\n' "$name" "$val"

    # rc files disagreeing is a real failure mode — a half-applied edit, or a
    # hand-tweak to one file. Never let it hide behind a last-wins read.
    if [ "$conflict" -eq 1 ]; then
      printf '      \033[31mCONFLICT: rc files disagree -> %s\033[0m\n' "$where"
      printf '      \033[31mre-run 2-shell-and-conda.sh to make them consistent\033[0m\n'
    else
      printf '      written to:  %s\n' "$(printf '%s' "$where" | sed 's/=[^,]*//g')"
    fi

    # Live means: this shell already has it, with the value the rc file sets.
    if [ -n "${!name-}" ] && [ "${!name-}" = "$val" ]; then
      printf '      in shell:    \033[32myes\033[0m\n'
    elif [ -n "${!name-}" ]; then
      printf '      in shell:    \033[33mdiffers\033[0m (currently %s)\n' "${!name}"
    else
      printf '      in shell:    \033[33mnot yet\033[0m\n'
    fi

    # A typo'd path does not error — it silently creates a second empty cache
    # the first time something writes to it. Surface it now.
    case "$val" in
      /*) if [ -d "$val" ]; then printf '      path:        exists\n'
          else printf '      path:        \033[31mDOES NOT EXIST\033[0m\n'; fi ;;
    esac
  done

  # conda writes its own block; report it but never touch it.
  local conda_rcs=""
  for rc in "${rcs[@]}"; do
    [ -f "$rc" ] || continue
    grep -q '>>> conda initialize >>>' "$rc" && conda_rcs="${conda_rcs:+$conda_rcs, }$(basename "$rc")"
  done
  [ -n "$conda_rcs" ] && printf '\n  \033[90m+ conda initialize block in %s (managed by conda, not us)\033[0m\n' "$conda_rcs"

  # Only nag about reloading if something is actually stale.
  local stale=0
  for name in "${names[@]}"; do
    [ -n "${!name-}" ] || stale=1
  done
  if [ "$stale" -eq 1 ]; then
    printf '\n  \033[90mNot live in this shell yet. Load it with:  source ~/.bashrc   (or: exec zsh)\033[0m\n'
  fi
  printf '\n'
}
