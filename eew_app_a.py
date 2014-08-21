#!/usr/bin/env python
# eew_app.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
ModuleName = "eew_app" 

import sys
import os.path
import time
import logging
from cbcommslib import CbApp
from cbconfig import *
import requests
import json
from twisted.internet import reactor

# Sensor enables and min changes that will register. Can be overridden in environment
TEMP                     = str2bool(os.getenv('EEW_TEMP', 'True'))
IRTEMP                   = str2bool(os.getenv('EEW_IRTEMP', 'False'))
ACCEL                    = str2bool(os.getenv('EEW_ACCEL', 'False'))
HUMIDITY                 = str2bool(os.getenv('EEW_HUMIDITY', 'False'))
GYRO                     = str2bool(os.getenv('EEW_GYRO', 'False'))
MAGNET                   = str2bool(os.getenv('EEW_MAGNET', 'False'))
BUTTONS                  = str2bool(os.getenv('EEW_BUTTONS', 'False'))
BINARY                   = str2bool(os.getenv('EEW_BINARY', 'True'))
LUMINANCE                = str2bool(os.getenv('EEW_LUMINANCE', 'True'))
TEMP_MIN_CHANGE          = float(os.getenv('EEW_TEMP_MIN_CHANGE', '0.2'))
IRTEMP_MIN_CHANGE        = float(os.getenv('EEW_IRTEMP_MIN_CHANGE', '0.5'))
HUMIDITY_MIN_CHANGE      = float(os.getenv('EEW_HUMIDITY_MIN_CHANGE', '0.5'))
LUMINANCE_MIN_CHANGE     = float(os.getenv('EEW_LUMINANCE_MIN_CHANGE', '1.0'))
ACCEL_MIN_CHANGE         = float(os.getenv('EEW__ACCEL_MIN_CHANGE', '0.02'))
GYRO_MIN_CHANGE          = float(os.getenv('EEW_GYRO_MIN_CHANGE', '0.5'))
MAGNET_MIN_CHANGE        = float(os.getenv('EEW_MAGNET_MIN_CHANGE', '1.5'))
SLOW_POLLING_INTERVAL    = float(os.getenv('EEW_SLOW_POLLING_INTERVAL', '120.0'))
FAST_POLLING_INTERVAL    = float(os.getenv('EEW_FAST_POLLING_INTERVAL', '3.0'))
USER                     = "ea2f0e06ff8123b7f46f77a3a451731a"
SEND_DELAY               = 20  # Time to gather values for a device before sending them

class DataManager:
    """ Managers data storage for all sensors """
    def __init__(self, bridge_id):
        self.baseurl = "http://geras.1248.io/series/" + bridge_id + "/"
        self.s={}
        self.waiting=[]

    def sendValuesThread(self, values, deviceID):
        url = self.baseurl + deviceID
        status = 0
        logging.debug("%s sendValues, device: %s length: %s", ModuleName, deviceID, str(len(values)))
        headers = {'Content-Type': 'application/json'}
        try:
            r = requests.post(url, auth=(USER, ''), data=json.dumps({"e": values}), headers=headers)
            status = r.status_code
            success = True
        except:
            success = False
        if status !=200 or not success:
            logging.debug("%s sendValues failed, status: %s", ModuleName, status)
            # On error, store the values that weren't sent ready to be sent again
            reactor.callFromThread(self.storeValues, values, deviceID)

    def sendValues(self, deviceID):
        values = self.s[deviceID]
        # Call in thread as it may take a second or two
        self.waiting.remove(deviceID)
        del self.s[deviceID]
        reactor.callInThread(self.sendValuesThread, values, deviceID)

    def storeValues(self, values, deviceID):
        if not deviceID in self.s:
            self.s[deviceID] = values
        else:
            self.s[deviceID].append(values)
        if not deviceID in self.waiting:
            reactor.callLater(SEND_DELAY, self.sendValues, deviceID)
            self.waiting.append(deviceID)

    def storeAccel(self, deviceID, timeStamp, a):
        values = [
                  {"n":"accel_x", "v":accel[0], "t":timeStamp},
                  {"n":"accel_y", "v":accel[1], "t":timeStamp},
                  {"n":"accel_z", "v":accel[2], "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeTemp(self, deviceID, timeStamp, temp):
        values = [
                  {"n":"temperature", "v":temp, "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeIrTemp(self, deviceID, timeStamp, temp):
        values = [
                  {"n":"ir_temperature", "v":temp, "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeHumidity(self, deviceID, timeStamp, h):
        values = [
                  {"n":"humidity", "v":h, "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeButtons(self, deviceID, timeStamp, buttons):
        values = [
                  {"n":"left_button", "v":buttons["leftButton"], "t":timeStamp},
                  {"n":"right_button", "v":buttons["rightButton"], "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeGyro(self, deviceID, timeStamp, gyro):
        values = [
                  {"n":"gyro_x", "v":gyro[0], "t":timeStamp},
                  {"n":"gyro_y", "v":gyro[1], "t":timeStamp},
                  {"n":"gyro_z", "v":gyro[2], "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeMagnet(self, deviceID, timeStamp, magnet):
        values = [
                  {"n":"magnet_x", "v":magnet[0], "t":timeStamp},
                  {"n":"magnet_y", "v":magnet[1], "t":timeStamp},
                  {"n":"magnet_z", "v":magnet[2], "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeBinary(self, deviceID, timeStamp, b):
        values = [
                  {"n":"binary", "v":b, "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

    def storeLuminance(self, deviceID, timeStamp, v):
        values = [
                  {"n":"luminance", "v":v, "t":timeStamp}
                 ]
        self.storeValues(values, deviceID)

class Accelerometer:
    def __init__(self, id):
        self.previous = [0.0, 0.0, 0.0]
        self.id = id

    def processAccel(self, resp):
        accel = [resp["data"]["x"], resp["data"]["y"], resp["data"]["z"]]
        timeStamp = resp["timeStamp"]
        event = False
        for a in range(3):
            if abs(accel[a] - self.previous[a]) > ACCEL_MIN_CHANGE:
                event = True
                break
        if event:
            self.dm.storeAccel(self.id, timeStamp, accel)
            self.previous = accel

class TemperatureMeasure():
    """ Either send temp every minute or when it changes. """
    def __init__(self, id):
        # self.mode is either regular or on_change
        self.mode = "on_change"
        self.minChange = 0.2
        self.id = id
        epochTime = time.time()
        self.prevEpochMin = int(epochTime - epochTime%60)
        self.currentTemp = 0.0

    def processTemp (self, resp):
        timeStamp = resp["timeStamp"] 
        temp = resp["data"]
        if self.mode == "regular":
            epochMin = int(timeStamp - timeStamp%60)
            if epochMin != self.prevEpochMin:
                temp = resp["data"]
                self.dm.storeTemp(self.id, self.prevEpochMin, temp) 
                self.prevEpochMin = epochMin
        else:
            if abs(temp-self.currentTemp) >= TEMP_MIN_CHANGE:
                self.dm.storeTemp(self.id, timeStamp, temp) 
                self.currentTemp = temp

class IrTemperatureMeasure():
    """ Either send temp every minute or when it changes. """
    def __init__(self, id):
        # self.mode is either regular or on_change
        self.mode = "on_change"
        self.minChange = 0.2
        self.id = id
        epochTime = time.time()
        self.prevEpochMin = int(epochTime - epochTime%60)
        self.currentTemp = 0.0

    def processIrTemp (self, resp):
        timeStamp = resp["timeStamp"] 
        temp = resp["data"]
        if self.mode == "regular":
            epochMin = int(timeStamp - timeStamp%60)
            if epochMin != self.prevEpochMin:
                temp = resp["data"]
                self.dm.storeIrTemp(self.id, self.prevEpochMin, temp) 
                self.prevEpochMin = epochMin
        else:
            if abs(temp-self.currentTemp) >= IRTEMP_MIN_CHANGE:
                self.dm.storeIrTemp(self.id, timeStamp, temp) 
                self.currentTemp = temp

class Buttons():
    def __init__(self, id):
        self.id = id

    def processButtons(self, resp):
        timeStamp = resp["timeStamp"] 
        buttons = resp["data"]
        self.dm.storeButtons(self.id, timeStamp, buttons)

class Gyro():
    def __init__(self, id):
        self.id = id
        self.previous = [0.0, 0.0, 0.0]

    def processGyro(self, resp):
        gyro = [resp["data"]["x"], resp["data"]["y"], resp["data"]["z"]]
        timeStamp = resp["timeStamp"] 
        event = False
        for a in range(3):
            if abs(gyro[a] - self.previous[a]) > GYRO_MIN_CHANGE:
                event = True
                break
        if event:
            self.dm.storeGyro(self.id, timeStamp, gyro)
            self.previous = gyro

class Magnet():
    def __init__(self, id):
        self.id = id
        self.previous = [0.0, 0.0, 0.0]

    def processMagnet(self, resp):
        mag = [resp["data"]["x"], resp["data"]["y"], resp["data"]["z"]]
        timeStamp = resp["timeStamp"] 
        event = False
        for a in range(3):
            if abs(mag[a] - self.previous[a]) > MAGNET_MIN_CHANGE:
                event = True
                break
        if event:
            self.dm.storeMagnet(self.id, timeStamp, mag)
            self.previous = mag

class Humid():
    """ Either send temp every minute or when it changes. """
    def __init__(self, id):
        self.id = id
        self.previous = 0.0

    def processHumidity (self, resp):
        h = resp["data"]
        timeStamp = resp["timeStamp"] 
        if abs(h-self.previous) >= HUMIDITY_MIN_CHANGE:
            self.dm.storeHumidity(self.id, timeStamp, h) 
            self.previous = h

class Binary():
    def __init__(self, id):
        self.id = id
        self.previous = 0

    def processBinary(self, resp):
        timeStamp = resp["timeStamp"] 
        b = resp["data"]
        if b == "on":
            bi = 1
        else:
            bi = 0
        if bi != self.previous:
            self.dm.storeBinary(self.id, timeStamp-1.0, self.previous)
            self.dm.storeBinary(self.id, timeStamp, bi)
            self.previous = bi

class Luminance():
    def __init__(self, id):
        self.id = id
        self.previous = 0

    def processLuminance(self, resp):
        v = resp["data"]
        timeStamp = resp["timeStamp"] 
        if abs(v-self.previous) >= LUMINANCE_MIN_CHANGE:
            self.dm.storeLuminance(self.id, timeStamp, v) 
            self.previous = v

class App(CbApp):
    def __init__(self, argv):
        logging.basicConfig(filename=CB_LOGFILE,level=CB_LOGGING_LEVEL,format='%(asctime)s %(message)s')
        self.appClass = "monitor"
        self.state = "stopped"
        self.status = "ok"
        self.accel = []
        self.gyro = []
        self.magnet = []
        self.temp = []
        self.irTemp = []
        self.buttons = []
        self.humidity = []
        self.binary = []
        self.luminance = []
        self.devices = []
        self.devServices = [] 
        self.idToName = {} 
        #CbApp.__init__ MUST be called
        CbApp.__init__(self, argv)

    def setState(self, action):
        if action == "clear_error":
            self.state = "running"
        else:
            self.state = action
        logging.debug("%s state: %s", ModuleName, self.state)
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def onConcMessage(self, resp):
        #logging.debug("%s resp from conc: %s", ModuleName, resp)
        if resp["resp"] == "config":
            msg = {
               "msg": "req",
               "verb": "post",
               "channel": int(self.id[3:]),
               "body": {
                        "msg": "services",
                        "appID": self.id,
                        "idToName": self.idToName,
                        "services": self.devServices
                       }
                  }
            self.sendMessage(msg, "conc")
        else:
            msg = {"appID": self.id,
                   "msg": "error",
                   "message": "unrecognised response from concentrator"}
            self.sendMessage(msg, "conc")

    def onAdaptorData(self, message):
        """
        This method is called in a thread by cbcommslib so it will not cause
        problems if it takes some time to complete (other than to itself).
        """
        #logging.debug("%s onadaptorData, message: %s", ModuleName, message)
        if message["characteristic"] == "acceleration":
            for a in self.accel:
                if a.id == self.idToName[message["id"]]: 
                    a.processAccel(message)
                    break
        elif message["characteristic"] == "temperature":
            for t in self.temp:
                if t.id == self.idToName[message["id"]]:
                    t.processTemp(message)
                    break
        elif message["characteristic"] == "ir_temperature":
            for t in self.irTemp:
                if t.id == self.idToName[message["id"]]:
                    t.processIrTemp(message)
                    break
        elif message["characteristic"] == "gyro":
            for g in self.gyro:
                if g.id == self.idToName[message["id"]]:
                    g.processGyro(message)
                    break
        elif message["characteristic"] == "magnetometer":
            for g in self.magnet:
                if g.id == self.idToName[message["id"]]:
                    g.processMagnet(message)
                    break
        elif message["characteristic"] == "buttons":
            for b in self.buttons:
                if b.id == self.idToName[message["id"]]:
                    b.processButtons(message)
                    break
        elif message["characteristic"] == "humidity":
            for b in self.humidity:
                if b.id == self.idToName[message["id"]]:
                    b.processHumidity(message)
                    break
        elif message["characteristic"] == "binary_sensor":
            for b in self.binary:
                if b.id == self.idToName[message["id"]]:
                    b.processBinary(message)
                    break
        elif message["characteristic"] == "luminance":
            for b in self.luminance:
                if b.id == self.idToName[message["id"]]:
                    b.processLuminance(message)
                    break

    def onAdaptorService(self, message):
        #logging.debug("%s onAdaptorService, message: %s", ModuleName, message)
        self.devServices.append(message)
        serviceReq = []
        for p in message["service"]:
            # Based on services offered & whether we want to enable them
            if p["characteristic"] == "temperature":
                if TEMP:
                    self.temp.append(TemperatureMeasure((self.idToName[message["id"]])))
                    self.temp[-1].dm = self.dm
                    serviceReq.append({"characteristic": "temperature",
                                       "interval": SLOW_POLLING_INTERVAL})
            elif p["characteristic"] == "ir_temperature":
                if IRTEMP:
                    self.irTemp.append(IrTemperatureMeasure(self.idToName[message["id"]]))
                    self.irTemp[-1].dm = self.dm
                    serviceReq.append({"characteristic": "ir_temperature",
                                       "interval": SLOW_POLLING_INTERVAL})
            elif p["characteristic"] == "acceleration":
                if ACCEL:
                    self.accel.append(Accelerometer((self.idToName[message["id"]])))
                    serviceReq.append({"characteristic": "acceleration",
                                       "interval": FAST_POLLING_INTERVAL})
                    self.accel[-1].dm = self.dm
            elif p["characteristic"] == "gyro":
                if GYRO:
                    self.gyro.append(Gyro(self.idToName[message["id"]]))
                    self.gyro[-1].dm = self.dm
                    serviceReq.append({"characteristic": "gyro",
                                       "interval": FAST_POLLING_INTERVAL})
            elif p["characteristic"] == "magnetometer":
                if MAGNET: 
                    self.magnet.append(Magnet(self.idToName[message["id"]]))
                    self.magnet[-1].dm = self.dm
                    serviceReq.append({"characteristic": "magnetometer",
                                       "interval": FAST_POLLING_INTERVAL})
            elif p["characteristic"] == "buttons":
                if BUTTONS:
                    self.buttons.append(Buttons(self.idToName[message["id"]]))
                    self.buttons[-1].dm = self.dm
                    serviceReq.append({"characteristic": "buttons",
                                       "interval": 0})
            elif p["characteristic"] == "humidity":
                if HUMIDITY:
                    self.humidity.append(Humid(self.idToName[message["id"]]))
                    self.humidity[-1].dm = self.dm
                    serviceReq.append({"characteristic": "humidity",
                                       "interval": SLOW_POLLING_INTERVAL})
            elif p["characteristic"] == "binary_sensor":
                if BINARY:
                    self.binary.append(Binary(self.idToName[message["id"]]))
                    self.binary[-1].dm = self.dm
                    serviceReq.append({"characteristic": "binary_sensor",
                                       "interval": 0})
            elif p["characteristic"] == "luminance":
                if LUMINANCE:
                    self.luminance.append(Luminance(self.idToName[message["id"]]))
                    self.luminance[-1].dm = self.dm
                    serviceReq.append({"characteristic": "luminance",
                                       "interval": 0})
        msg = {"id": self.id,
               "request": "service",
               "service": serviceReq}
        self.sendMessage(msg, message["id"])
        self.setState("running")

    def onConfigureMessage(self, config):
        """ Config is based on what sensors are available """
        for adaptor in config["adaptors"]:
            adtID = adaptor["id"]
            if adtID not in self.devices:
                # Because configure may be re-called if devices are added
                name = adaptor["name"]
                friendly_name = adaptor["friendly_name"]
                logging.debug("%s Configure app. Adaptor name: %s", ModuleName, name)
                self.idToName[adtID] = friendly_name.replace(" ", "_")
                self.devices.append(adtID)
        self.dm = DataManager(self.bridge_id)
        self.setState("starting")

if __name__ == '__main__':
    App(sys.argv)
