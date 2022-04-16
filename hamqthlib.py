#!/usr/bin/env python3
#
# File: hamqthlib.py
#
# Module for accessing the hamqth.com XML database
# loosely based on qrz.py by Martin Ewing
#
# Copyright (c) 2013 Steve Conklin
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

import xml.dom.minidom as mdom
import urllib.request, sys, getopt, getpass, os

from os                  import path
from json                import dumps, dump, load

# AGENT is the program name that's passed to hamqth, in order to
# identify the application. You may add further information
# by including a string applicationID when you instantiate the class
# This string (if provided) will be prepended to the AGENT string
AGENT = 'hamqthpy0.01'

LOGIN_URL1 = 'http://www.hamqth.com/xml.php?u='
LOGIN_URL2 = '&p='

CALL_QUERY_URL  = 'http://www.hamqth.com/xml.php?id=%s&callsign=%s&prg=%s'
BIO_QUERY_URL = 'http://www.hamqth.com/xml_bio.php?id=%s&callsign=%s&strip_html=1'
RECENT_ACTIVITY_QUERY_URL = 'http://www.hamqth.com/xml_recactivity.php?id=%s&callsign=%s&rec_activity=1&log_activity=1&logook=1'

DXCC_QUERY_URL = 'http://www.hamqth.com/dxcc.php?callsign=U3AP'


MAX_LOGIN_TRIAL = 3     # How many times to retry login

FPATH = os.environ.get('HOME')+'/.'+AGENT       # User's init file

class QTHNoLogin(Exception):
    pass

class QTHLoginFailed(Exception):
    pass

class QTHLookupFailed(Exception):
    pass

class QTHCallsignNotFound(Exception):
    pass

class QTH():
    """
    This class encapsulates hamqth.com lookups

    When instantiating the class, several options are available:
       configPath - provides the path to a file which may hold login username and password
       maxLogins - defines the maximum number of retries for failing logins
       storeCredentials - if True, then credentials will be stored in the config file
       applicationID - A string identifying your application, supplied to hamqth.com
    """

    # __init__
    #
    def __init__(self, configPath=FPATH, maxLogins=MAX_LOGIN_TRIAL, storeCredentials = False, applicationID = ''):
        appid_clean =  "".join(c for c in applicationID if c.isalnum() or c==' ').rstrip()
        self.cfg_path = configPath + '-' + appid_clean
        self.username = None
        self.password = None
        self.sessionID = None
        self.max_logins = maxLogins
        self.appID = applicationID + ':' + AGENT
        self.store_creds = storeCredentials

        # if we're to store credentials, try to open them
        # if not then delete any we have
        if self.store_creds:
            self.__readStoredCredentials()
        else:
            self.__removeStoredCredentials()

    def __readStoredCredentials(self):
        try:
            with open(self.cfg_path) as f:
                jdata = load(f)
                self.username = jdata['u']
                self.password = jdata['p']
                if 'sid' in jdata:
                    self.sessionID = jdata['sid']
                else:
                    self.sessionID = None # force getting a new session ID

        except Exception as e:
            pass

    def __writeStoredCredentials(self):
        if not self.store_creds:
            return

        if (self.username is None) or (self.password is None):
            raise ValueError("Attempt to save credentials which haven't been set")

        cdata = {}
        cdata['u'] = self.username
        cdata['p'] = self.password
        if self.sessionID is not None:
            cdata['sid'] = self.sessionID
        with open(self.cfg_path, 'w') as f:
            dump(cdata, f)
        os.chmod(self.cfg_path,0o0600) # a little security

    def __removeStoredCredentials(self):
        if path.exists(self.cfg_path):
            os.remove(self.cfg_path)

    def __getSessionId(self):

        if self.username is None:
            raise QTHNoLogin("HamQTH username and password have not been set")

        login_url = LOGIN_URL1+self.username+LOGIN_URL2+self.password

        for query_trial in range(self.max_logins):
            wd =  urllib.request.urlopen(login_url)
            content = wd.read()
            wd.close()
            doc = mdom.parseString(content)            # Construct DOM w/ Python heavy lifting

            rt = doc.documentElement        # Find root element
            Session_D =  self.__getInfo(rt, 'session')
            if Session_D is None:
                raise ValueError('Did not find a session element in a request for session ID')
            else:
                if 'session_id' in Session_D:
                    self.sessionID = Session_D['session_id']
                    self.__writeStoredCredentials()
                    return
                elif 'error' in Session_D:
                    raise QTHLoginFailed(Session_D['error'])
                else:
                    raise ValueError('Did not find session_id or error in session element')
        else:                                   # End of 'for' loop, no success
            raise QTHLookupFailed("number of query attempts exceeded")

    # getInfo collects data into dictionary from XML
    def __getInfo(self, rt, tag_name):
        Ans_D = {}
        rtelements = rt.getElementsByTagName(tag_name)
        if len(rtelements) < 1: 
            return None     # error
        s_elems = rtelements[0].getElementsByTagName('*')
        for s in s_elems:
            for ss in s.childNodes:
                # Ignore if not a text node...
                if ss.nodeName == '#text':
                    Ans_D[s.nodeName] = ss.nodeValue
        return Ans_D

    def __makeAuthenticatedGet(self, callsign, query_type):
        if self.sessionID is None:
            self.__getSessionId()
        for query_trial in range(self.max_logins):
            if query_type == "CALL":
                url = CALL_QUERY_URL %  (self.sessionID, callsign, self.appID)
            elif query_type == "BIO":
                url = BIO_QUERY_URL %  (self.sessionID, callsign)
            elif query_type == "ACTIVITY":
                url = RECENT_ACTIVITY_QUERY_URL %  (self.sessionID, callsign)
            else:
                raise ValueError("Unexpected query type")

            wd =  urllib.request.urlopen(url)
            content = wd.read()
            wd.close()
            try:
                doc = mdom.parseString(content)            # Construct DOM w/ Python heavy lifting
            except:
                # Failed to parse
                print("Failed to Parse XML")
                return None

            # if successful, 'search' is in the results
            # if bad session id, 'session' is in the results, and session/error = 
            # if callsign not found, 'session' is in the results, and session/error = "Callsign not found"

            rt = doc.documentElement        # Find root element
            Search_D =  self.__getInfo(rt, 'search')
            if Search_D is not None:
                # Success
                res = self.__getInfo(rt, 'search')  # Place XML data into friendly dictionary
                return res

            # If we didn't get search results, we need to dig deeper
            Session_D =  self.__getInfo(rt, 'session')

            if Session_D is not None:
                # This is an error
                errText = Session_D['error']
                if errText == 'Callsign not found':
                    raise QTHCallsignNotFound
                elif errText == 'Session does not exist or expired':
                    self.__getSessionId()
                else:
                    raise ValueError(errText)
            else:
                raise ValueError('Did not get session or search in response')
        else:                                   # End of 'for' loop, no success
            raise QTHLookupFailed("number of query attempts exceeded")

    def setLoginInfo(self, username=None, password=None, storeCredentials = None):
        """
        Set the login credentials and save them if requested.
        if storeCredentials is supplied, the setting overrides the current one
        """
        if (username is None) or (password is None):
            raise ValueError('Username and password must be supplied')
        self.username = username
        self.password = password
        if storeCredentials is not None:
            if storeCredentials:
                self.store_creds = True
            else:
                self.store_creds = False
                self.__removeStoredCredentials()
        self.sessionID = None # force getting a new session ID
        self.__writeStoredCredentials()

    def loginInfoExists(self):
        """
        Returns True if we have login user and password set
        This can be called after instantiating the class with
        storeCredentials = True, to see whether stored credentials
        were retrieved.
        """
        if (self.username is None) or (self.password is None):
            return False
        return True

    def lookupCallsign(self, callsign, getCallsignInfo = True, getBio = False, getActivity = False):
        results = {}
        if getCallsignInfo:
            res = self.__makeAuthenticatedGet(callsign, "CALL")
            if res is not None:
                results.update(res)
        if getBio:
            res = self.__makeAuthenticatedGet(callsign, "BIO")
            if res is not None:
                results.update(res)
        if getActivity:
            res = self.__makeAuthenticatedGet(callsign, "ACTIVITY")
            if res is not None:
                results.update(res)
            
        return results

