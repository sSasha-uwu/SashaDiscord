@echo off

git add .
git commit -m "update"
git push origin main

ssh rpi02n "SUDO_ASKPASS=123 && sudo -A -v && sudo systemctl restart discord-bots && journalctl -u discord-bots -f"