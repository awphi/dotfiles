#!/bin/bash
brew bundle --file=/dev/stdin <<EOF
brew "ripgrep"
brew "mise"
brew "starship"
brew "zsh-autosuggestions"
brew "gh"
brew "docker"
brew "docker-compose"
brew "docker-buildx"
brew "colima"
brew "flatbuffers"
brew "uv"
brew "htop"

cask "google-chrome"
cask "codex"
cask "visual-studio-code"
cask "spotify"
cask "font-hack-nerd-font"
cask "bitwarden"
cask "ghostty"
EOF
