# chrome-monitoring
monitors and blocks websites opened in Chrome

sudo pip3 install flask

sudo cp chrome-monitoring/server/chrome-monitoring.service /etc/systemd/system
sudo systemctl enable chrome-monitoring
sudo systemctl daemon-reload
sudo systemctl start chrome-monitoring