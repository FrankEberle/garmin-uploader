#!/usr/bin/env python3

'''
MIT License

Copyright (c) 2019 Frank Eberle // www.frank-eberle.de

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import dbus
import time
import os
import sys


class UDisks2:

	def __init__(self):
		self._bus = dbus.SystemBus()
		self._obj_manager = self._bus.get_object('org.freedesktop.UDisks2',
			'/org/freedesktop/UDisks2')


	def scan(self):
		objects = self._obj_manager.GetManagedObjects(dbus_interface="org.freedesktop.DBus.ObjectManager")
		self._drives = {}
		self._block_devices = {}
		for obj_name in objects:
			obj = self._bus.get_object('org.freedesktop.UDisks2', obj_name)
			if obj_name.startswith("/org/freedesktop/UDisks2/drives/"):
				self._drives[obj_name] = obj
			elif obj_name.startswith("/org/freedesktop/UDisks2/block_devices/"):
				self._block_devices[obj_name] = obj

	
	def _get_obj_by_prop(self, objects, iface_name, prop_name, prop_value):
		result = []
		for path, obj in objects.items():
			v = obj.Get(iface_name, prop_name, dbus_interface="org.freedesktop.DBus.Properties")
			if v == prop_value:
				result.append({
					"path": path,
					"obj": obj
				})
		return result


	def get_drives_by_prop(self, prop_name, prop_value):
		return self._get_obj_by_prop(self._drives, "org.freedesktop.UDisks2.Drive", prop_name, prop_value)


	def get_block_devices_by_prop(self, prop_name, prop_value):
		return self._get_obj_by_prop(self._block_devices, "org.freedesktop.UDisks2.Block", prop_name, prop_value)


	def mount(self, dev_path):
		mount_point = None
		obj = self._block_devices[dev_path]
		mount_points = obj.Get("org.freedesktop.UDisks2.Filesystem", "MountPoints", dbus_interface="org.freedesktop.DBus.Properties")
		if len(mount_points) > 0:
			mount_point = ""
			for b in mount_points[0]:
				if str(b) != "\0":
					mount_point += str(b)
		else:
			mount_point = obj.Mount({}, dbus_interface="org.freedesktop.UDisks2.Filesystem")
		return mount_point


	def umount(self, dev_path):
		obj = self._block_devices[dev_path]
		obj.Unmount({}, dbus_interface="org.freedesktop.UDisks2.Filesystem")



