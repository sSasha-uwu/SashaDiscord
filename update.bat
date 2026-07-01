@echo off

git add .
git commit -m "update"
git push origin main

ssh RPi02W@192.168.20.15 "echo "RPi02W" | sudo -S -v && echo "RPi02W" | sudo -S systemctl restart discordbots && echo "RPi02W" | sudo -S journalctl -u discordbots -f"