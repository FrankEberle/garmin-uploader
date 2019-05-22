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

from setuptools import setup, find_packages


setup(
	name="garmin-unloader",
	version="1.0",
	description="Tool to upload activities from Garmin Forerunner to Garmin Connect",
	author="Frank Eberle",
	author_email="develop@frank-eberle.de",
	url="https://github.com/FrankEberle/garminuploader",
	packages=find_packages(),
	scripts=[
		"bin/garmin-uploader"
	],
	install_requires=[
		"dbus-python",
		"Garmin_Connect_activity_exporter>=1.0.0"
	],
	dependency_links=[
		"git+https://github.com/FrankEberle/garminexport#egg=Garmin_Connect_activity_exporter-1.0.0",
    ],
)