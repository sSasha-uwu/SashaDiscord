git add .
git commit -m "update"
git push origin main

ssh rpi02n << EOF
    SUDO_ASKPASS=~/sudo.sh
    sudo -A -v
    sudo systemctl restart discord-bots
    journalctl -u discord-bots -f
EOF