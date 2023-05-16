import subprocess

# ssid = "MickeyMouse"
# passkey = "MinnieMouse"

def create_wpa_supplicant(ssid, passkey):
	# Backup existing wpa_supplicant.conf
	command_backup = ["sudo", "cp", "/etc/wpa_supplicant/wpa_supplicant.conf", "/etc/wpa_supplicant/wpa_supplicant.conf.bak"]
	subprocess.run(command_backup)

	# Create a new empty wpa_supplicant.conf
	with open('/etc/wpa_supplicant/wpa_supplicant.conf', 'w', encoding="utf-8") as f:
		f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
		f.write("update_config=1\n\n")

	p1 = subprocess.Popen(
		["wpa_passphrase", ssid, passkey],
		stdout=subprocess.PIPE
	)

	p2 = subprocess.Popen(
		["sudo", "tee", "-a", "/etc/wpa_supplicant/wpa_supplicant.conf"],
		stdin=p1.stdout,
		stdout=subprocess.PIPE
	)

	p1.stdout.close()  # Give p1 a SIGPIPE if p2 dies.

	output,err = p2.communicate()

if __name__ == "__main__":
	create_wpa_supplicant("MickeyMouse", "MinnieMouse")

