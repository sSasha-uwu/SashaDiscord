@echo off

git add .
git commit -m "update"
git push origin main

putty -ssh RPi02W@192.168.20.15 -pw RPi02W "echo "RPi02W" | sudo -S -v && echo "RPi02W" | sudo -S systemctl restart discordbots && echo "RPi02W" | sudo -S journalctl -u discordbots -f"