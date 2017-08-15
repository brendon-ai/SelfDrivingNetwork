#!/usr/bin/env python2

from os import system, popen, listdir
from time import time
from threading import Thread
from pexpect import pxssh
from evdev import InputDevice, categorize, ecodes, KeyEvent

recording_encoder = False

def handle_gamepad_input():
	global recording_encoder
	gamepad = InputDevice('/dev/input/by-id/usb-Logitech_Logitech_Dual_Action_E89BB55E-event-joystick')
	for event in gamepad.read_loop():
		if event.type == ecodes.EV_KEY:
			keyevent = categorize(event)
			print keyevent.keycode
			if keyevent.keycode == "BTN_THUMB":
				recording_encoder = True
			elif keyevent.keycode == "BTN_THUMB2":
				recording_encoder = False


system('gst-launch-1.0 -v v4l2src device=/dev/video1 ! image/jpeg, width=320, height=180, framerate=30/1 ! jpegparse ! multifilesink location="/tmp/sim%d.jpg" &')

system('rm /tmp/sim*.jpg')

s = pxssh.pxssh()
s.login('192.168.0.230', 'admin', '')

thread = Thread(target=handle_gamepad_input)
thread.daemon = True
thread.start()
i = 0

while True:
	i += 1
	values_to_jetson = (int(recording_encoder), 0, i)
	values_str = ''
	for value in values_to_jetson:
		values_str += (str(value) + '\n')
	values_str = values_str[:-1]
	s.sendline('printf "%s" > /home/lvuser/temp.txt' % values_str)
	s.sendline('mv /home/lvuser/temp.txt /home/lvuser/values.txt')
	if recording_encoder:
		s.sendline('cat /home/lvuser/latest.encval')
		s.prompt()
		last_max_file = -1
		for line in iter(s.before.splitlines()):
			if 'out' in line:
				encoder_value = float(line[3:])
				print encoder_value
				max_file = last_max_file
				for file_name in listdir("/tmp"):
					if "sim" in file_name and ".jpg" in file_name:
						file_number = int(file_name[3:-4])
						if file_number > max_file:
							max_file = file_number
				if max_file > -1:
					system('mv /tmp/sim%d.jpg /tmp/%f_sim%d.jpg' % (max_file, encoder_value, max_file))
				last_max_file = max_file
				break

