#!/usr/bin/env python3
#
# File: apitest.py
#
# Copyright (c) 2021 Ben Kuhn
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  
# 02110-1301, USA.
#

from sys import argv
import getpass
import json
from hamqthlib import *

def queryLoginInfo():
    print('Please provide your login info for the hamqth.com service...')
    username = input('Username: ')
    password = getpass.getpass('Password: ')
    return (username, password)


if len(sys.argv) != 2:
    print("usage:\n\nargv[0] callsign")

qth = QTH(storeCredentials = True, applicationID = 'apitest')

if not qth.loginInfoExists():
    uname, passw = queryLoginInfo()
    qth.setLoginInfo(username=uname, password=passw, storeCredentials=True)

results = qth.lookupCallsign(argv[1], getBio=False, getActivity=False)
#results = json.loads(qth.lookupCallsign(argv[1], getBio=False, getActivity=False))
#callsign, getCallsignInfo = True, getBio = False, getActivity = False):
#for key in results:
#    print("%s : %s" % (key, results[key]))

#print(results["nick"])

band = "40M"
mode = "FT8"
freq = "14.074000"
qso_date = "20220415"
time_on = "170000"
time_off = "170100"
rst_rcvd = "-10"
rst_sent = "+11"
qsl_rcvd = "N"
qsl_sent = "N"
country = results["country"]
gridsquare = results["grid"]
name = results["nick"]
# check if it exists in the record first I suppose
cnty = results["us_county"]
state = results["us_state"]

cont = results["continent"]
# Again, check if state exists
qth = results["adr_city"] + ", " + state

cladif = "<call:" + str(len(argv[1])) + ">" + argv[1] + "<band:" + str(len(band)) + ">" + band + "<mode:" + str(len(mode)) + ">" + mode + "<freq:" + str(len(freq)) + ">" + freq + "<qso_date:" + str(len(qso_date)) + ">" + str(qso_date) + "<time_on:" + str(len(time_on)) + ">" + str(time_on) + "<time_off:" + str(len(time_off)) + ">" + str(time_off) + "<rst_rcvd:" + str(len(rst_rcvd)) + ">" + str(rst_rcvd) + "<qsl_rcvd:" + str(len(qsl_rcvd)) + ">" + qsl_rcvd +"<qsl_sent:" + str(len(qsl_sent)) + ">" + qsl_sent + "<country:" + str(len(country)) + ">" + country + "<gridsquare:" + str(len(gridsquare)) + ">" + gridsquare + "<name:" + str(len(name)) + ">" + name + "<cnty:" + str(len(cnty)) + ">" + cnty + "<state:" + str(len(state)) + ">" + state + "<cont:" + str(len(cont)) + ">" + cont + "<qth:" + str(len(qth)) + ">" + qth + "<eor>"


toCL = {
    "key": "YOUR_API_KEY",
    "station_profile_id": "Station Profile ID Number",
    "type": "adif",
    "string": cladif
}

print(toCL)
