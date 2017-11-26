#!/usr/bin/python3
# coding: utf-8
#
# A Bitbar implementation for linux
#
# Author:  <maxisabattini@gmail.com>
# Fork Homepage: https://github.com/maxisabattini/bytebar
# License: GPL v3
#
import logging
import os
import sys
import tempfile

from pathlib import Path
import subprocess
import re
from pprint import pprint
import base64

import gi
from gi.repository import GLib, Gtk

logging.basicConfig(level=logging.INFO)

class BytebarSI(object):

    config_path=".config/argos"

    def __init__(self):

        self.ind={}

        files = os.listdir( str(Path.home()) + "/" + self.config_path)
        for cfilename in files:
            i=self.get_indicator_for_file(cfilename)
            if i:
                self.ind[cfilename]=i
                if self.ind[cfilename].milliseconds > 0:
                    GLib.timeout_add(self.ind[cfilename].milliseconds, self.timeout, cfilename)

        pprint("Loaded indicators")
        pprint(self.ind)

        ##
        # After load initial indicators, timeout watching files changes
        # comparing each indicator milisecond changed
        #
        GLib.timeout_add(1000, self.watchfiles)  

    def is_exe(self, fpath):
        return os.access(fpath, os.X_OK) 

    def watchfiles(self):
        files = os.listdir( str(Path.home()) + "/" + self.config_path)
        for cfilename in files:

            if cfilename in self.ind.keys():
                m=self._get_milliseconds(cfilename)
                if not self.ind[cfilename].milliseconds == m:
                    ind.milliseconds=m
                if not self.is_exe(str(Path.home()) + "/" + self.config_path + "/" + cfilename):
                    self.ind[cfilename].set_visible(False)
                else:
                    self.ind[cfilename].set_visible(True)
            else:
                i=self.get_indicator_for_file(cfilename)
                if i:
                    self.ind[cfilename]=i
                    if self.ind[cfilename].milliseconds > 0:
                        GLib.timeout_add(self.ind[cfilename].milliseconds, self.timeout, cfilename)
        return True
                        

    def timeout(self, cfilename):
        pprint( "Refreshing: " + cfilename)

        if not self.is_exe( str(Path.home()) + "/" + self.config_path + "/" + cfilename ):
            return False

        cfile = str(Path.home()) + "/" + self.config_path+"/"+cfilename
        cfileoutput = subprocess.getoutput(cfile)

        self.ind[cfilename].cfileoutput=cfileoutput
        self.load_indicator( self.ind[cfilename])

        return True


    def get_indicator_for_file(self, cfilename):

        if not self.is_exe(str(Path.home()) + "/" + self.config_path + "/" + cfilename):
            return

        cfile = str(Path.home()) + "/" + self.config_path+"/"+cfilename
        cfileoutput = subprocess.getoutput(cfile)

        ind = Gtk.StatusIcon()
        ind.cfilename=cfilename
        ind.cfileoutput=cfileoutput
        ind.milliseconds=self._get_milliseconds(cfilename)
        self.load_indicator(ind)
        return ind
  

    def load_indicator(self, ind):    

        lines = ind.cfileoutput.split("\n")

        ## First line / Title
        line=lines.pop(0)
        options = line.split("|")
        label=options.pop(0)
        options=''.join(options)
        options=self._get_options(options)
        
        options["icon_file"] = ""       
        if options["image"]:
          fn, tindicator = tempfile.mkstemp(suffix="")

          with open(tindicator, "wb") as f:                    
            f.write(base64.b64decode( options["image"] ))
            f.close()
          
          options["icon_file"]=tindicator


        if options["icon_name"] :
          ind.set_from_icon_name(options["icon_name"])
          
        if options["icon_file"] :
          ind.set_from_file(options["icon_file"])

        ind.set_visible(True)

        self.create_menu(ind)

        ind.connect_pid=ind.connect("popup_menu", self.on_tray_popup_menu)
        ind.connect_aid=ind.connect("activate", self.on_tray_activate)        

    def on_tray_popup_menu(self, widget, button, time, data = None):        
        widget.menu.popup(None, None, None, widget, 3, time)        

    def on_tray_activate(self, widget):
        widget.menu.popup(None, None, None, widget, 3, Gtk.get_current_event_time())

    def create_menu(self, ind):

        if not ind.cfileoutput:
                return

        lines = ind.cfileoutput.split("\n")
        
        line=lines.pop(0)

        # First separator
        line=lines.pop(0)
        ## End First line / Title

        # create menu {{{
        menu = Gtk.Menu()

        if lines[len(lines)-1]=="---":
                lines.pop()        
        
        for line in lines:

            options = line.split("|")
            label=options.pop(0)
            label=label.strip()

            if label == "---":
                menu.add(Gtk.SeparatorMenuItem())
            else:
                menu.add( self._get_item(label, ''.join(options) ) )
                
        
        menu.add(Gtk.SeparatorMenuItem())

        menu.add( self._get_item( ind.cfilename, ' size=8 ') )

        menu.add(Gtk.SeparatorMenuItem())

        iexit=self._get_item( "Quit", ' size=9 ')
        iexit.connect('activate', self.on_exit)
        menu.add(iexit)
        
        menu.show_all()
        # }}} menu done!

        ind.menu=menu

    def _get_milliseconds(self, cfilename):

        milliseconds=0

        regex = r"\.([0-9][0-9]?)s\."
        m = re.search(regex, cfilename)
        if  m :
            milliseconds=int( m.group(1) ) * 1000


        regex = r"\.([0-9][0-9]?)m\."
        m = re.search(regex, cfilename)
        if  m :
            milliseconds=int( m.group(1) ) * 60000

        regex = r"\.([0-9][0-9]?)h\."
        m = re.search(regex, cfilename)
        if  m :
            milliseconds=int( m.group(1) ) * 3600000


        regex = r"\.([0-9][0-9]?)h\."
        m = re.search(regex, cfilename)
        if  m :
            milliseconds=int( m.group(1) ) * 86400000

        return milliseconds

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
            'color': self._parse_option(p_options, "color"),
            'font': self._parse_option(p_options, "font"),
            'size': self._parse_option(p_options, "size")            
        }

        return options

    def _add_separator(self, menu):

        box = Gtk.HBox(spacing=2)
        box.pack_start(Gtk.SeparatorMenuItem(),False, False, 4 )
        
        cont = Gtk.MenuItem()
        cont.add(box)

        menu.add(cont)        

    def _get_item(self, p_label, p_options):

        options=self._get_options( p_options )

        box = Gtk.HBox(spacing=2)

        if not options["icon_name"] == "":
            img = Gtk.Image.new_from_icon_name(options["icon_name"], Gtk.IconSize.MENU)
            box.pack_start(img,False, False, 4 )
            img.show()

        label=Gtk.Label(p_label)

        markup=""
        if not options["color"] == "":            
            markup=markup+" color='"+options["color"]+"' "
        if not options["font"] == "":            
            markup=markup+" font_family='"+options["font"]+"' "
        if not options["size"] == "":            
            markup=markup+" font='"+options["size"]+"' "

        if not markup == "":
            markup="<span "+markup+">" + p_label + '</span>'            
            label.set_markup(markup)

        box.pack_start(label,False, False, 4 )
        
        cont = Gtk.MenuItem()
        cont.p_command=options["command"]
        cont.p_terminal=options["terminal"]
        cont.p_href=options["href"]        
        cont.connect('activate', self.on_item_activated)        
        
        cont.add(box)

        return cont
        
    def on_item_activated(self, widget):
        
        if widget.p_href:
            os.system( "xdg-open " + widget.p_href + " &")
            return

        command=widget.p_command

        if not widget.p_terminal == "false":
            command="gnome-terminal -e \"" + command + "\""                    

        if not widget.p_command == "":
            os.system(command + " &")

    def on_exit(self, event=None, data=None):
        """Action call when the main programs is closed."""

        logging.info("Terminated")

        try:
            Gtk.main_quit()
        except RuntimeError:
            pass


if __name__ == "__main__":

    app = BytebarSI()
    try:
        Gtk.main()
    except KeyboardInterrupt:
        app.on_exit()
