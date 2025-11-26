# adamwph (awphi) dotfiles

The following is a collection of my dotfiles, which I use to configure my development environment across all my machines.

# Requirements

- MacOS
- Homebrew
- Git

# Installation

One-liner for fresh machines:

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install chezmoi && chezmoi init --apply --verbose awphi/dotfiles
```

If you've already got `brew` and `chezmoi` installed, you can simply run:

```sh
chezmoi init --apply --verbose awphi/dotfiles
```

> **Note:** If applying to a new machine for the first time, ensure you log in to Bitwarden Desktop and enabled the SSH agent for access to secrets.

# Updating source state

- Regular files: use `chezmoi add` (or just `chezmoi re-add` if only editing files already in source state)
- VSCode extensions: re-run `sh .bin/save-code-extensions.sh` after installing/uninstalling any extensions
