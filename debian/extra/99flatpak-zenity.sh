#! /bin/bash
if zenity --question --text 'Would you like to upgrade all flatpak packages?'
then
	x-terminal-emulator -e bash -c "flatpak upgrade -y"
	x-terminal-emulator -e pkexec bash -c "flatpak upgrade -y"
	zenity --info --text 'All flatpak packages have been updated.'
fi
