#!/bin/bash
brew bundle --file=/dev/stdin <<EOF
brew "ripgrep"
brew "mise"
brew "starship"
brew "zsh-autosuggestions"
brew "gh"
brew "docker"
brew "docker-compose"
brew "colima"
brew "xz" # required to install qlty

cask "google-chrome"
cask "codex"
cask "visual-studio-code"
cask "spotify"
cask "font-hack-nerd-font"
cask "bitwarden"
cask "kitty"
EOF

curl https://qlty.sh | bash