#!/bin/bash

code --list-extensions | sort | sed -e "s/\(.*\)/\"\1\"/" > "$(chezmoi source-path)/.chezmoitemplates/code-extensions.tmpl"