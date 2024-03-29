#!/usr/bin/python3
# coding: utf-8
#
# A simple indicator applet displaying cpu and memory information
#
# Author: Alex Eftimie <alex@eftimie.ro>
# Fork Author: fossfreedom <foss.freedom@gmail.com>
# Original Homepage: http://launchpad.net/indicator-sysmonitor
# Fork Homepage: https://github.com/fossfreedom/indicator-sysmonitor
# License: GPL v3
#
import logging
import os
import sys
import tempfile
from argparse import ArgumentParser
from gettext import gettext as _
from gettext import bindtextdomain, textdomain
from threading import Event

from pathlib import Path
import subprocess
import re
from pprint import pprint
import base64

import gi
gi.require_version('AppIndicator3', '0.1')
from gi.repository import AppIndicator3 as appindicator
from gi.repository import GLib, Gtk

#from preferences import VERSION, Preferences
#from sensors import SensorManager

textdomain("indicator-sysmonitor")
bindtextdomain("indicator-sysmonitor", "./lang")

GLib.threads_init()
logging.basicConfig(level=logging.INFO)

HELP_MSG = """<span underline="single" size="x-large">{title}</span>

{introduction}

{basic}
• cpu: {cpu_desc}
• mem: {mem_desc}
• bat<i>%d</i>: {bat_desc}
• net: {net_desc}
• upordown: {upordown_desc}
• publicip: {publicip_desc}

{compose}
• fs//<i>mount-point</i> : {fs_desc}

<big>{example}</big>
CPU {{cpu}} | MEM {{mem}} | root {{fs///}}
""".format(
    title=_("Help Page"),
    introduction=_("The sensors are the names of the devices you want to \
    retrieve information from. They must be placed between brackets."),
    basic=_("The basics are:"),
    cpu_desc=_("It shows the average of CPU usage."),
    mem_desc=_("It shows the physical memory in use."),
    bat_desc=_("It shows the available battery which id is %d."),
    net_desc=_("It shows the amount of data you are downloading and uploading \
    through your network."),
    upordown_desc=_("It shows whether your internet connection is up or down \
     - the sensor is refreshed every 10 seconds."),
    publicip_desc=_("It shows your public IP address \
     - the sensor is refreshed every 10 minutes."),
    compose=_("Also there are the following sensors that are composed with \
    two parts divided by two slashes."),
    fs_desc=_("Show available space in the file system."),
    example=_("Example:"))


class IndicatorSysmonitor(object):

    config_path=".config/argos"
    terminal_apps=[ "konsole", "mate-terminal", "gnome-terminal" ]
    terminal_app="xterm"

    def __init__(self):

        home = str(Path.home())

        files=["argos.sh","tools.sh"]

        self.ind=[]
        
        files = os.listdir(home + "/" + self.config_path)
        for cfilename in files:            
            self.ind.append( self._get_menu_for_file(cfilename) )

        for term in self.terminal_apps:
            output = subprocess.getoutput("which " + term + " 1> /dev/null; echo $?")
            pprint(term)
            pprint(output)
            if(output=="0"):
                self.terminal_app=subprocess.getoutput("which " + term)

        pprint(self.terminal_app)

    def _get_menu_for_file(self, cfilename):

        home = str(Path.home())
        cfile = home + "/" + self.config_path+"/"+cfilename
        cfileoutput = subprocess.getoutput(cfile)
        
        #Check file executable
        if cfileoutput.find("Permission denied") >= 0:
            return

        pprint(cfileoutput)

        logging.info("OUT: " + cfileoutput)
        
        # create menu {{{
        menu = Gtk.Menu()

        lines = cfileoutput.split("\n")

        #pprint(lines)

        ## First line / Title

        line=lines.pop(0)
        options = line.split("|")
        label=options.pop(0)
        options=''.join(options)
        options=self._get_options(options)
               
        if options["icon_name"] == "":
            options["icon_name"]=""

            if options["image"] == "":
                options["image"] = options["templateImage"]

            if options["image"] == "":
                options["image"] = "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
	    
            if not options["image"] == "":

                logging.info("image: " + options["image"])
                fn, tindicator = tempfile.mkstemp(suffix="")

                with open(tindicator, "wb") as f:                    
                    f.write(base64.b64decode( options["image"] ))
                    f.close()
                options["icon_name"]=tindicator
                

        ind = appindicator.Indicator.new("bytebar-"+cfilename, options["icon_name"], appindicator.IndicatorCategory.APPLICATION_STATUS)
        #ind.set_ordering_index(0)
        ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        ind.set_label(label,"")

        # First separator
        line=lines.pop(0)
        ## End First line / Title

        for line in lines:

            options = line.split("|")
            label=options.pop(0)
            label=label.strip()

            if label == "---":
                menu.add(Gtk.SeparatorMenuItem())
            else:
                menu.add( self._get_item(label, ''.join(options) ) )

        menu.add(Gtk.SeparatorMenuItem())

        menu.add( self._get_item( cfilename, ' size=8 ') )

        menu.add(Gtk.SeparatorMenuItem())

        iexit=self._get_item( "Quit", ' size=10 ')
        iexit.connect('activate', self.on_exit)
        menu.add(iexit)
        
        menu.show_all()
        # }}} menu done!

        ind.set_menu(menu)   
        
        return ind

    def _parse_option(self, options, o):

        value=""
        m = re.search(o+"=([^ ]*)", options)
        if  m :
            value=m.group(1)
        m = re.search(o+"='([^']*)", options)
        if  m :
            value=m.group(1)
        m = re.search(o+"=\"([^\"]*)", options)
        if  m :
            value=m.group(1)

        return value

    def _get_options(self, p_options):

        options = {
            'icon_name': self._parse_option(p_options, "iconName"),
            'command': self._parse_option(p_options, "bash"),
            'terminal': self._parse_option(p_options, "terminal"),
            'href': self._parse_option(p_options, "href"),            
            'image': self._parse_option(p_options, "image"),
            'templateImage': self._parse_option(p_options, "templateImage"),
            'color': self._parse_option(p_options, "color"),
            'font': self._parse_option(p_options, "font"),
            'size': self._parse_option(p_options, "size")            
        }

        return options

    def _add_separator(self, menu):
        #menu.add(Gtk.SeparatorMenuItem())

        box = Gtk.HBox(spacing=2)
        box.pack_start(Gtk.SeparatorMenuItem(),False, False, 4 )
        
        cont = Gtk.MenuItem()
        cont.add(box)


        menu.add(cont)        

    def _get_item_pango(self, p_label, p_options):

        options=self._get_options( p_options )

        box = Gtk.HBox(spacing=6)

        if not options["icon_name"] == "":
            img = Gtk.Image.new_from_icon_name(options["icon_name"], Gtk.IconSize.MENU)
            box.pack_start(img, False, False, 4 )
            img.show()

        label=Gtk.Label(label=p_label)

        markup=""
        if not options["color"] == "":            
            markup=markup+" color='"+options["color"]+"' "
        if not options["font"] == "":            
            markup=markup+" font_family='"+options["font"]+"' "
        if not options["size"] == "":            
            markup=markup+" font='"+options["size"]+"' "

        if not markup == "":
            markup="<span "+markup+">" + p_label + '</span>'
            pprint("Markup: " + markup)
            label.set_markup(markup)

        box.pack_start(label, False, False, 4 )
        
        cont = Gtk.MenuItem()
        cont.p_command=options["command"]
        cont.p_terminal=options["terminal"]
        cont.p_href=options["href"]        
        cont.connect('activate', self.on_item_activated)        
        
        cont.add(box)
        cont.show_all()

        #menu.add(cont)

        return cont

    def _get_item(self, p_label, p_options):

        options=self._get_options( p_options )

        markup=""
        if not options["color"] == "":            
            markup=markup+" color='"+options["color"]+"' "
        if not options["font"] == "":            
            markup=markup+" font_family='"+options["font"]+"' "
        if not options["size"] == "":            
            markup=markup+" font='"+options["size"]+"' "

        if markup:
            markup="<span "+markup+">" + p_label + '</span>'
        
        if not markup:
            markup=p_label        
        
        cont = Gtk.ImageMenuItem(p_label)
                
        if not options["icon_name"] == "":
            img = Gtk.Image.new_from_icon_name(options["icon_name"], Gtk.IconSize.MENU)
            cont.set_image(img)
            cont.set_always_show_image(True)
            img.show()        
        
        cont.p_command=options["command"]
        cont.p_terminal=options["terminal"]
        cont.p_href=options["href"]        
        cont.connect('activate', self.on_item_activated)

        cont.show_all()

        return cont
        
    def on_item_activated(self, widget):
        
        if widget.p_href:
            cmd="xdg-open \"" + widget.p_href.replace("\\'", "") + "\" &"
            pprint("cmd: " + widget.p_href)
            os.system( cmd )
            return

        command=widget.p_command

        if not widget.p_terminal == "false":
            command=self.terminal_app + " -e \"" + command + "\""                    

        if not widget.p_command == "":
            os.system(command + " &")

    def popup_menu(self, *args):
        self.popup.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def on_exit(self, event=None, data=None):
        """Action call when the main programs is closed."""

        logging.info("Terminated")

        try:
            Gtk.main_quit()
        except RuntimeError:
            pass

class IndicatorSysmonitor2(object):

    def __init__(self):
        self._preferences_dialog = None
        self._help_dialog = None

        fn, self.tindicator = tempfile.mkstemp(suffix=".svg")

        with open(self.tindicator, "w") as f:
            svg = '<?xml version="1.0" encoding="UTF-8" \
                        standalone="no"?><svg id="empty" xmlns="http://www.w3.org/2000/svg" \
                        height="22" width="1" version="1.0" \
                        xmlns:xlink="http://www.w3.org/1999/xlink"></svg>'
            f.write(svg)
            f.close()

        self.ind = appindicator.Indicator.new("indicator-sysmonitor", self.tindicator, \
                                              appindicator.IndicatorCategory.SYSTEM_SERVICES)
        self.ind.set_ordering_index(0)

        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_label("Init...", "")

        self._create_menu()

        self.alive = Event()
        self.alive.set()

        #self.sensor_mgr = SensorManager()
        #self.load_settings()

    def _create_menu(self):
        """Creates the main menu and shows it."""
        # create menu {{{
        menu = Gtk.Menu()
        # add System Monitor menu item
        full_sysmon = Gtk.MenuItem(_('System Monitor'))
        full_sysmon.connect('activate', self.on_full_sysmon_activated)
        menu.add(full_sysmon)
        menu.add(Gtk.SeparatorMenuItem())

        # add preferences menu item
        pref_menu = Gtk.MenuItem(_('Preferences'))
        pref_menu.connect('activate', self.on_preferences_activated)
        menu.add(pref_menu)

        # add help menu item
        help_menu = Gtk.MenuItem(_('Help'))
        help_menu.connect('activate', self._on_help)
        menu.add(help_menu)

        # add preference menu item
        exit_menu = Gtk.MenuItem(_('Quit'))
        exit_menu.connect('activate', self.on_exit)
        menu.add(exit_menu)

        menu.show_all()

        pprint(self.ind)
        self.ind.set_menu(menu)
        logging.info("Menu shown")
        # }}} menu done!

    def update_indicator_guide(self):

        guide = self.sensor_mgr.get_guide()

        self.ind.set_property("label-guide", guide)

    def update(self, data):
        # data is the dict of all sensors and their values
        # { name, label }

        # look through data and find out if there are any icons to be set
        for sensor in data:
            test_str = data[sensor].lower()
            if "use_icon" in test_str:
                path = data[sensor].split(":")[1]
                self.ind.set_icon_full(path, "")
                # now strip the icon output from data so that it is not displayed
                remaining = test_str.split("use_icon")[0].strip()
                if not remaining:
                    remaining = " "

                data[sensor] = remaining

            if "clear_icon" in test_str:
                self.ind.set_icon_full(self.tindicator, "")

                remaining = test_str.split("clear_icon")[0].strip()
                if not remaining:
                    remaining = " "

                data[sensor] = remaining

        label = self.sensor_mgr.get_label(data)

        self.ind.set_label(label.strip(), "")
        self.ind.set_title(label.strip())

    def load_settings(self):

        self.sensor_mgr.load_settings()
        self.sensor_mgr.initiate_fetcher(self)
        self.update_indicator_guide()

    # @staticmethod
    def save_settings(self):
        self.sensor_mgr.save_settings()

    # actions raised from menu
    def on_preferences_activated(self, event=None):
        """Raises the preferences dialog. If it's already open, it's
        focused"""
        if self._preferences_dialog is not None:
            self._preferences_dialog.present()
            return

        self._preferences_dialog = Preferences(self)
        self._preferences_dialog.run()
        self._preferences_dialog = None

    def on_full_sysmon_activated(self, event=None):
        os.system('gnome-system-monitor &')

    def on_exit(self, event=None, data=None):
        """Action call when the main programs is closed."""
        # cleanup temporary indicator icon
        os.remove(self.tindicator)
        # close the open dialogs
        if self._help_dialog is not None:
            self._help_dialog.destroy()

        if self._preferences_dialog is not None:
            self._preferences_dialog.destroy()

        logging.info("Terminated")
        self.alive.clear()  # DM: why bother with Event() ???

        try:
            Gtk.main_quit()
        except RuntimeError:
            pass

    def _on_help(self, event=None, data=None):
        """Raise a dialog with info about the app."""
        if self._help_dialog is not None:
            self._help_dialog.present()
            return

        self._help_dialog = Gtk.MessageDialog(
            None, Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, None)

        self._help_dialog.set_title(_("Help"))
        self._help_dialog.set_markup(HELP_MSG)
        self._help_dialog.run()
        self._help_dialog.destroy()
        self._help_dialog = None

if __name__ == "__main__":

    # setup an instance with config
    app = IndicatorSysmonitor()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        app.on_exit()
