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

# Updating source state

- Regular files: use `chezmoi add`
- VSCode extensions: re-run `sh .bin/save-code-extensions.sh` after installing/uninstalling any extensions
