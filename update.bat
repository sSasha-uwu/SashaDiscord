@echo off

git add .
git commit -m "update"
git push origin main

ssh RPi02W@192.168.20.15 "echo "RPi02W" | sudo -A -v && sudo systemctl restart discord-bots && journalctl -u discord-bots -f"