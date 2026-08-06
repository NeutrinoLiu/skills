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
# Usage: env_block_write <rcfile> 'VAR=value' ['PATH+=/some/dir' ...]
#
# The PATH+= form prepends a directory instead of overwriting, and guards on
# membership so re-sourcing an rc file inside one shell cannot stack duplicates.
env_block_write() {
  local rc="$1"; shift
  [ -f "$rc" ] || return 0
  sed -i "\|$MARK_START|,\|$MARK_END|d" "$rc"
  {
    printf '\n%s\n' "$MARK_START"
    local kv dir
    for kv in "$@"; do
      case "$kv" in
        PATH+=*)
          dir="${kv#PATH+=}"
          # Trailing marker comment is what env_report parses back out.
          printf 'case ":$PATH:" in *":%s:"*) ;; *) export PATH="%s:$PATH" ;; esac  # path: %s\n' \
            "$dir" "$dir" "$dir"
          ;;
        *)
          printf 'export %s="%s"\n' "${kv%%=*}" "${kv#*=}"
          ;;
      esac
    done
    printf '%s\n' "$MARK_END"
  } >> "$rc"
}

# Print every variable this setup manages, where it is written, whether it is
# live in the current shell, and whether the path it names exists.
env_report() {
  local rcs=("$HOME/.bashrc" "$HOME/.zshrc")
  local names=() dirs=() rc line name val dir

  for rc in "${rcs[@]}"; do
    [ -f "$rc" ] || continue
    while IFS= read -r line; do
      case "$line" in
        *'# path: '*)
          dir="${line##*# path: }"
          case " ${dirs[*]-} " in *" $dir "*) ;; *) dirs+=("$dir") ;; esac
          ;;
        export\ *=*)
          name="${line#export }"; name="${name%%=*}"
          case " ${names[*]-} " in *" $name "*) ;; *) names+=("$name") ;; esac
          ;;
      esac
    done < <(sed -n "\|$MARK_START|,\|$MARK_END|p" "$rc")
  done

  printf '\n\033[1mEnvironment managed by this setup\033[0m\n'

  if [ ${#names[@]} -eq 0 ] && [ ${#dirs[@]} -eq 0 ]; then
    printf '  \033[90m(nothing yet — 2-shell-and-conda.sh writes the first block)\033[0m\n\n'
    return 0
  fi

  # One block per variable rather than a table: paths are long and unbounded,
  # and a column layout silently mangles them.
  for name in ${names[@]+"${names[@]}"}; do
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

  # PATH entries are prepends, not assignments, so they are reported by
  # membership rather than by value — a string compare against $PATH would
  # always read as "differs" and mean nothing.
  for dir in ${dirs[@]+"${dirs[@]}"}; do
    local where=""
    for rc in "${rcs[@]}"; do
      [ -f "$rc" ] || continue
      sed -n "\|$MARK_START|,\|$MARK_END|p" "$rc" | grep -qF "# path: $dir" \
        && where="${where:+$where, }$(basename "$rc")"
    done

    printf '\n  \033[1mPATH\033[0m + %s\n' "$dir"
    printf '      written to:  %s\n' "$where"

    case ":$PATH:" in
      *":$dir:"*) printf '      in shell:    \033[32myes\033[0m\n' ;;
      *)          printf '      in shell:    \033[33mnot yet\033[0m\n' ;;
    esac

    if [ -d "$dir" ]; then
      printf '      path:        exists'
      # An empty ~/.local/bin means the tool that was supposed to land there
      # never did — worth saying, since the PATH entry itself looks healthy.
      [ -x "$dir/claude" ] && printf ' (claude found)'
      printf '\n'
    else
      printf '      path:        \033[31mDOES NOT EXIST\033[0m\n'
    fi
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
  for name in ${names[@]+"${names[@]}"}; do
    [ -n "${!name-}" ] || stale=1
  done
  for dir in ${dirs[@]+"${dirs[@]}"}; do
    case ":$PATH:" in *":$dir:"*) ;; *) stale=1 ;; esac
  done
  if [ "$stale" -eq 1 ]; then
    printf '\n  \033[90mNot live in this shell yet. Load it with:  source ~/.bashrc   (or: exec zsh)\033[0m\n'
  fi
  printf '\n'
}
