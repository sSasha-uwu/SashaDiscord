git add .
git commit -m "update"
git push origin master
ssh rpi02n
SUDO_ASKPASS=~/sudo.sh
sudo -A -v
sudo systemctl restart discord-bots
journalctl -u discord-bots -f