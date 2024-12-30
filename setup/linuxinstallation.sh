echo "Installing dependencies. Please wait."
sudo apt install python3-wxgtk4.0
sudo apt install python3-matplotlib
sudo apt install python3-markdown
sudo apt install python3-pyperclip
sudo apt install python3-psutil
sudo apt install python3-requests
echo "Installed all dependencies."
echo "Running XediX."
python3 main.py
echo "Later, use linuxrun.sh for running."
chmod +x linuxrun.sh
