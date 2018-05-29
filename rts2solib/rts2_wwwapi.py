
from __future__ import print_function
import requests
import json
from .baseclasses import Config
from bs4 import BeautifulSoup
import re

"""This module is a wrapper for the HTTP/JSON based rts2api
That is part of the core of the RTS2 C++ stuff written by 
Petr Kubanek. There is also python interface to this 
in the RTS2 github repo but it is not fully functional. 
We will probably be porting much of that in here and 
adding functionality as we go. 
"""

class rts2_value(object):
    # value types
    varflags = (
            ("RTS2_VALUE_WRITABLE" , 0x02000000),
            ("RTS2_VALUE_BASETYPE" , 0x0000000f),
            ("RTS2_VALUE_STRING" , 0x00000001),
            ("RTS2_VALUE_INTEGER" , 0x00000002),
            ("RTS2_VALUE_TIME" , 0x00000003),
            ("RTS2_VALUE_DOUBLE" , 0x00000004),
            ("RTS2_VALUE_FLOAT" , 0x00000005),
            ("RTS2_VALUE_BOOL" , 0x00000006),
            ("RTS2_VALUE_SELECTION" , 0x00000007),
            ("RTS2_VALUE_LONGINT" , 0x00000008),
            ("RTS2_VALUE_RADEC" , 0x00000009),
            ("RTS2_VALUE_ALTAZ" , 0x0000000A),
            ("RTS2_VALUE_STAT" , 0x00000010),
            ("RTS2_VALUE_MMAX" , 0x00000020),
            ("RTS2_VALUE_STAT" , 0x10),

        )

    def __init__(self, name, info):
        self.name = name
        self.flags = info[0]
        self.i1 = info[1]
        self.i2 = info[2]
        self.i3 = info[3]
        self.description = info[4]
        self.writable = bool(self.flagdefs()['RTS2_VALUE_WRITABLE'] & self.flags )


    def flagdefs(self):
        return dict(self.varflags)

    def __repr__( self ):
        return "<rts2_value {}:\t{}>".format(self.name, self.description)

    def __str__(self):
        return self.__repr__()


    def printflags(self):
        for fname, hx in dict(self.varflags).iteritems():
            print(fname, (self.flags & hx) == hx )



class rts2comm(object):

    def __init__(self, debug=False):
        self.cfg = Config()
        self.devlist = self.cfg['device_list']
        self.baseurl = self.cfg['rts2url']
        self.auth = (self.cfg["username"], self.cfg['password'] )
        self.debug = debug

        self.flags = {
            "RTS2_VALUE_WRITABLE" : 0x02000000,
            "RTS2_VALUE_BASETYPE" : 0x0000000f,
            "RTS2_VALUE_STRING" : 0x00000001,
            "RTS2_VALUE_INTEGER" : 0x00000002,
            "RTS2_VALUE_TIME" : 0x00000003,
            "RTS2_VALUE_DOUBLE" : 0x00000004,
            "RTS2_VALUE_FLOAT" : 0x00000005,
            "RTS2_VALUE_BOOL" : 0x00000006,
            "RTS2_VALUE_SELECTION" : 0x00000007,
            "RTS2_VALUE_LONGINT" : 0x00000008,
            "RTS2_VALUE_RADEC" : 0x00000009,
            "RTS2_VALUE_ALTAZ" : 0x0000000A,
            "RTS2_VALUE_STAT" : 0x00000010,
            "RTS2_VALUE_MMAX" : 0x00000020,
            "RTS2_VALUE_STAT" : 0x10,
        }

        
    def get_device_info(self, device):
        """
        args: device -> name of the device

        Description: Uses RTS2 HTTP interface to get a json object of all the rts2 values
            (the ones you see in rts2-mon) of a device

        returns json with device data or error message
        """
        assert device in self.devlist, "This device {} is not in the device list in the config file".format(device)
        url = "{base}/api/get?e=1&d={dev}".format( base=self.baseurl, dev=device )
        try:
            r = requests.get( url, 
                    auth=self.auth )
            data = json.loads(r.text)
        except Exception as err:
            data = {"error": str(err)}

        return data



    def get_device_info_all( self ):
        """Same as device info but return data on all the devices"""
        return {device:self.get_device_info(device) for device in self.devlist}
           

    def set_rts2_value(self, device, name, value):
        """
        args:
            device -> name of the device
            name -> name of the value to be set ie queue_only
            value -> value to set it to

        Description:  uses rts2 http interface to set an RTS2 value.

        returns json with device data or error messag
        """
        
        try:
            data = self._set( d=device, v=value, n=name )
        except Exception as err:
            data = {"error": str(err)}

        return data

    

    def _converse( self, route, **kwargs ):
        url = "{}/{}".format(self.baseurl, route)
        r=requests.get(url, params=kwargs, auth=self.auth)
        if self.debug:
            print(r.url)
        return json.loads(r.text)

    def _set(self, **kwargs):
        return self._converse( 'api/set', **kwargs )

    def _get(self, **kwargs):
        return self._converse( 'api/get', **kwargs )

    def _getall( self ):
        return self._converse('api/getall', e=1)

    def _deviceinfo(self, device):
        return self._converse('api/deviceinfo', d=device)

    def get_state( self ):
        url = "{}/switchstate".format( self.cfg['rts2url'] )
        r=requests.get(url, auth=self.auth)
        
        soup = BeautifulSoup(r.text, 'lxml')
        regex = re.compile('Current state is:\s*(.*)$')
        for ptag in soup.find_all('p'):
            text = ptag.text
            found = regex.search(text)
            print( found )
            if found:
                return found.group(1)

    def set_state(self, state ):
        assert state.lower() in ["on", 'off', 'standby'], "new state must be on, off or standby"

        url = "{}/switchstate/{}".format(self.baseurl, state.lower())
        r=requests.get(url, auth=self.auth)

    def getrv(self):
        return rts2_value


