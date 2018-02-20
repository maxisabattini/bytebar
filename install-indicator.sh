#!/bin/bash

sed "s@~@$HOME@gi" $HOME/.local/share/bytebar/bytebar-indicator.desktop > $HOME/.local/share/applications/bytebar-indicator.desktop
chmod +x $HOME/.local/share/applications/bytebar-indicator.desktop
