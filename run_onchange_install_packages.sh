#!/bin/sh

# CLI tools
brew install ripgrep
brew install --cask codex
brew install colima
brew install zsh-autosuggestions

# Mise
brew install mise
mise install

# https://mise.jdx.dev/configuration.html#idiomatic-version-files
mise settings add idiomatic_version_file_enable_tools python
mise settings add idiomatic_version_file_enable_tools node
mise settings add idiomatic_version_file_enable_tools go

# Terminal prompt
brew install starship

# Editors
brew install --cask zed

# Fonts
brew install --cask font-hack-nerd-font
