#!/usr/bin/python3
#
# requires apt install python3-tk
# requires pip3 install SoCo
# requires pip3 install Pillow
#
# Sonos display in X11 naked window of a fixed dimension
# Designed to run full screen on a raspberry pi or similar device
#
# matt@corddry.com | 2021-05
#

import soco
import tkinter as tk
from PIL import Image, ImageTk, ImageColor, ImageDraw, ImageFont
from tkinter.ttk import Frame, Button, Style

import os
import sys
import syslog
import time

class ImageShow():
    def __init__(self):
        self.root = tk.Tk()

        #
        # SETTINGS
        #
        # window dimensions
        self.img_width = 320
        self.img_height = 240

        # override window size and use full screen
        self.fullscreen = 1

        # delay between refreshes in msec
        self.delay_active = 250
        self.delay_idle = 1000
        self.delay = self.delay_active

        # backlight control (if desired)
        self.do_backlight = 1 # enable
        self.backlight_off_time = 300 # seconds
        # path to command to set backlight at various levels
        self.backlight_low = "~/pitft22-backlight low"
        self.backlight_high = "~/pitft22-backlight high"
        self.backlight_off = "~/pitft22-backlight off"

        # default sonos to control if not specified as ARGV[1]
        selected_device = 'Living Room'

        #
        # END SETTINGS
        #

        syslog.syslog("Starting Sonos-X11")
        self.first_run = 1
        self.last_volume = 0
        self.last_source = ""
        self.last_state = ""
        self.backlight_state = ""
        self.backlight_low_time = time.time()

        # get actual screen geometry and enable fullscreen if requested and applicable
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        print("Screen is %d x %d" % (screen_w, screen_h))
        syslog.syslog("Screen is %d x %d" % (screen_w, screen_h))

        if self.fullscreen and (self.img_width < screen_w) and (self.img_height < screen_h):
            print(" - Full screen mode activated!")
            syslog.syslog("Full screen mode activated")
            self.img_width = screen_w
            self.img_height = screen_h

        # set window dimensions
        self.root.geometry("%dx%d+0+0" % (self.img_width, self.img_height))

        # which Sonos should we control?
        if len(sys.argv) > 1:
            selected_device = sys.argv[1]

        # discover sonos devices
        devices = {device.player_name: device for device in soco.discover()}

        # make sure the device exists
        if not(selected_device in devices.keys()):
            print("Error: Speaker",selected_device,"not found!\n\n")
            syslog.syslog(syslog.LOG_ERR,"Error: Speaker %s not found" % selected_device)
            sys.exit(1)

        # set the device object
        self.sonos = devices[selected_device]
        print("Found sonos",self.sonos.player_name)
        syslog.syslog("Found sonos %s" % self.sonos.player_name)
        self.set_backlight("high")
        self.render_image()
        self.display_image()
        self.root.after(self.delay, self.write_image)
        self.root.mainloop()

    def write_image(self):
        player_status = self.sonos.get_current_transport_info()
        status_change = 0
   
        # backlight control logic
        if player_status['current_transport_state'] == 'STOPPED':
            # backlight goes low, then off after a timeout
            if self.backlight_state == "high":
                self.set_backlight("low")
                self.backlight_low_time = time.time()
            elif self.backlight_state == "low":
                low_seconds = time.time() - self.backlight_low_time
                if low_seconds > self.backlight_off_time:
                    self.set_backlight("off")
        else:
            # backlight goes bright
            if self.backlight_state != "high":
                self.set_backlight("high")

        # trigger image redraw only when status changes
        if self.sonos.volume != self.last_volume:
            status_change = 1
        elif self.sonos.music_source != self.last_source:
            status_change = 1
        elif player_status['current_transport_state'] != self.last_state:
            status_change = 1

        if status_change:
            print("Status change:")
            print("- Device volume %d => %d" % (self.last_volume, self.sonos.volume))
            print("- Device source %s => %s" % (self.last_source, self.sonos.music_source))
            print("- Device status %s => %s" % (self.last_state, player_status['current_transport_state']))
            syslog.syslog("Status change: source %s volume %d status %s" \
                % (self.sonos.music_source, self.sonos.volume, \
                player_status['current_transport_state']))
            self.render_image()
            self.display_image()
            self.last_volume = self.sonos.volume
            self.last_source = self.sonos.music_source
            self.last_state = player_status['current_transport_state']

        # do it again
        self.root.after(self.delay, self.write_image)

    def render_image(self):
        with Image.new("RGB", (self.img_width, self.img_height), "#000000") as img:
            # make some text!
            txt = "%00d" % (self.sonos.volume)

            # get a font to be used
            fnt = ImageFont.truetype("Pillow/Tests/fonts/FreeSansBold.ttf", 200)

            # get a drawing context for the new image
            d = ImageDraw.Draw(img) 

            # draw text on the image
            d.text((self.img_width / 2, self.img_height * 0.45), txt, font=fnt,
                fill=(255,255,255,255), anchor="mm")


            fnt2 = ImageFont.truetype("Pillow/Tests/fonts/FreeSansBold.ttf", 24)

            # draw the device name and status (if playing) at the bottom
            # increase polling delay when player is idle,
            player_status = self.sonos.get_current_transport_info()
            player_text = self.sonos.player_name
            fnt2_color = (255, 192, 128, 255)
            if player_status['current_transport_state'] == 'STOPPED':
                self.delay = self.delay_idle
                
            else:
                self.delay = self.delay_active
                # only append player status if active
                player_text = "%s: %s" % (self.sonos.player_name, self.sonos.music_source)
                fnt2_color = (128, 255, 128, 255)


            d.text((self.img_width / 2, self.img_height * 0.94), player_text,
                font=fnt2, fill=fnt2_color, anchor="ms")
            syslog.syslog("Display: Volume %s Player %s" % (txt, player_text))

            # render the image via Tk
            self.image = ImageTk.PhotoImage(img)

    def display_image(self):
        # print("Display image")
        if self.first_run:
            self.panel = tk.Label(self.root, image=self.image)
            self.display = self.image
            self.panel.pack(side=tk.TOP, fill=tk.BOTH, expand=tk.YES)
            self.root.wm_attributes('-type', 'splash')
            self.first_run = 0
        else:
            self.panel.configure(image=self.image)
            self.display = self.image

    def set_backlight(self, level):
        if self.do_backlight:
            print(" - set backlight to %s" % level)
            syslog.syslog("Set backlight to %s" % level)
            if level == "low":
                os.system(self.backlight_low)
                self.backlight_state = "low"

            elif level == "high":
                os.system(self.backlight_high)
                self.backlight_state = "high"

            elif level == "off":
                os.system(self.backlight_off)
                self.backlight_state = "off"


def main():
    app = ImageShow()

if __name__ == '__main__':
    main()

