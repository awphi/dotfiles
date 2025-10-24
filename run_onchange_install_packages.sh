#!/bin/sh

# CLI tools
brew install ripgrep
brew install colima
brew install zsh-autosuggestions
brew install gh
brew install docker
brew install docker-compose

# Applications
brew install --cask codex
brew install --cask zed
brew install --cask google-chrome
brew install --cask spotify

# Fonts
brew install --cask font-hack-nerd-font

# Mise
brew install mise
mise install
# https://mise.jdx.dev/configuration.html#idiomatic-version-files
mise settings add idiomatic_version_file_enable_tools python
mise settings add idiomatic_version_file_enable_tools node
mise settings add idiomatic_version_file_enable_tools go

# Terminal prompt
brew install starship
