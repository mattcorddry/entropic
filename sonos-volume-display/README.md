# Sonos Volume Display

This project enables you to display full screen Sonos device status on an X11 driven
monitor. The project currently displays volume, device name, and source. This is
designed to run on a Raspberry Pi with a small built in LCD display, and includes
rudimentary backlight control so that the screen doesn't remain lit at all times.
However, it should work on anything which supports Python Tk based displays, and is
capable of running in a window for desktop use.

## Installation
Simple installation instructions. Assumes you know what you're doing :)

 1. Setup a simple Linux machine, such as a Raspberry Pi without X11.
 2. Setup the machine in *X11 kiosk* mode. I followed [this guide](https://blog.r0b.io/post/minimal-rpi-kiosk/)
 online and replaced `chromium` with `sonos-x11.py` in the `.xinitrc` file.
 3. Download `sonos-x11.py` to your home directory on the machine, make sure it's set as
 executable, such as `chmod 0755 ~/sonos-x11.py`.
 4. If you would like backlight control, create or adapt a script to do this. The script
 should take backlight levels `(low | medium | high | off)` as the only argument. I've
 supplied `pitft22-backlight` as an example, which controls the 
 [Adafruit PiTFT 2.2 LCD](https://learn.adafruit.com/adafruit-2-2-pitft-hat-320-240-primary-display-for-raspberry-pi).
 5. Edit `sonos-x11.py` where you will find settings around line 30.
 
## Examples

**.xinitrc**

	#!/usr/bin/env sh
	xset -dpms
	xset s off
	xset s noblank

	unclutter &
	if [ -x ~/sonos-x11.py ] ; then
    	while :; do
        	~/sonos-x11.py > /tmp/sonos-x11.out 2>&1
        	sleep 1
        	logger "Restarted sonos-x11.py on console"
    	done
	fi

**.bash_profile**

	# only run startx on local terminal
	if [ -z $DISPLAY ] && [ $(tty) = /dev/tty1 ]; then
		startx
	fi

## Reference Hardware

This is a simple parts list for my Raspberry Pi based volume display. YMMV.

 * [Raspberry Pi 3B+](https://www.amazon.com/CanaKit-Raspberry-Power-Supply-Listed/dp/B07BC6WH7V/)
 * [Zebra Bold Case](https://www.amazon.com/gp/product/B00UFEBYNS) _Requires some
modifications to fit the PiTFT screen below_
 * [Adafruit PiTFT 2.2 LCD](https://www.amazon.com/gp/product/B00S7GAVEO/) _Requires
 soldering of the 40-pin connector_
 * SD card of your choice for the root filesystem. Doesn't need much space.
 * To stand this up on a tabletop, I used:
   * [Angled MicroSD power cable](https://www.amazon.com/gp/product/B00ENZDFQ4/)
   * 10W+ USB-A power adapter
   * [Small plate stand](https://www.amazon.com/gp/product/B083DK2VTL/)
 