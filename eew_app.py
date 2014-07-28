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

# Sensor enables and min changes that will register. Can be overridden in environment
TEMP                     = str2bool(os.getenv('EEW_TEMP', 'True'))
IRTEMP                   = str2bool(os.getenv('EEW_IRTEMP', 'False'))
ACCEL                    = str2bool(os.getenv('EEW_ACCEL', 'False'))
HUMIDITY                 = str2bool(os.getenv('EEW_HUMIDITY', 'False'))
GYRO                     = str2bool(os.getenv('EEW_GYRO', 'False'))
MAGNET                   = str2bool(os.getenv('EEW_MAGNET', 'False'))
BUTTONS                  = str2bool(os.getenv('EEW_BUTTONS', 'False'))
TEMP_MIN_CHANGE          = float(os.getenv('EEW_TEMP_MIN_CHANGE', '0.2'))
IRTEMP_MIN_CHANGE        = float(os.getenv('EEW_IRTEMP_MIN_CHANGE', '0.5'))
HUMIDITY_MIN_CHANGE      = float(os.getenv('EEW_HUMIDITY_MIN_CHANGE', '0.5'))
ACCEL_MIN_CHANGE         = float(os.getenv('EEW__ACCEL_MIN_CHANGE', '0.02'))
GYRO_MIN_CHANGE          = float(os.getenv('EEW_GYRO_MIN_CHANGE', '0.5'))
MAGNET_MIN_CHANGE        = float(os.getenv('EEW_MAGNET_MIN_CHANGE', '1.0'))
SENSOR_POLLING_INTERVAL  = float(os.getenv('EEW_SENSOR_POLLING_INTERVAL', '30.0'))
USER                     = "ea2f0e06ff8123b7f46f77a3a451731a"


class DataManager:
    """ Managers data storage for all sensors """
    def __init__(self, bridge_id):
        self.baseurl = "http://geras.1248.io/series/" + bridge_id + "/"

    def sendValues(self, values, deviceID):
        url = self.baseurl + deviceID
        headers = {'Content-Type': 'application/json'}
        r = requests.post(url, auth=(USER, ''), data=json.dumps(values), headers=headers)

    def storeAccel(self, deviceID, timeStamp, a):
        values = { "e":[
                        {"n":"accel_x", "v":accel[0], "t":timeStamp},
                        {"n":"accel_y", "v":accel[1], "t":timeStamp},
                        {"n":"accel_z", "v":accel[2], "t":timeStamp}
                      ]
                 }    
        values =         self.sendValues(values, deviceID)

    def storeTemp(self, deviceID, timeStamp, temp):
        values = { "e":[
                        {"n":"temperature", "v":temp, "t":timeStamp}
                       ]
                 }    
        self.sendValues(values, deviceID)

    def storeIrTemp(self, deviceID, timeStamp, temp):
        values = { "e":[
                        {"n":"ir_temperature", "v":temp, "t":timeStamp}
                       ]
                 }    
        self.sendValues(values, deviceID)

    def storeHumidity(self, deviceID, timeStamp, h):
        values = { "e":[
                        {"n":"humidity", "v":h, "t":timeStamp}
                       ]
                 }    
        self.sendValues(values, deviceID)

    def storeButtons(self, deviceID, timeStamp, buttons):
        values = { "e":[
                        {"n":"left_button", "v":buttons["leftButton"], "t":timeStamp},
                        {"n":"right_button", "v":buttons["rightButton"], "t":timeStamp}
                      ]
                 }    
        self.sendValues(values, deviceID)

    def storeGyro(self, deviceID, timeStamp, gyro):
        values = { "e":[
                        {"n":"gyro_x", "v":gyro[0], "t":timeStamp},
                        {"n":"gyro_y", "v":gyro[1], "t":timeStamp},
                        {"n":"gyro_z", "v":gyro[2], "t":timeStamp}
                      ]
                 }    
        self.sendValues(values, deviceID)

    def storeMagnet(self, deviceID, timeStamp, magnet):
        values = { "e":[
                        {"n":"magnet_x", "v":magnet[0], "t":timeStamp},
                        {"n":"magnet_y", "v":magnet[1], "t":timeStamp},
                        {"n":"magnet_z", "v":magnet[2], "t":timeStamp}
                      ]
                 }    
        self.sendValues(values, deviceID)

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
        if message["content"] == "acceleration":
            for a in self.accel:
                if a.id == self.idToName[message["id"]]: 
                    a.processAccel(message)
                    break
        elif message["content"] == "temperature":
            for t in self.temp:
                if t.id == self.idToName[message["id"]]:
                    t.processTemp(message)
                    break
        elif message["content"] == "ir_temperature":
            for t in self.irTemp:
                if t.id == self.idToName[message["id"]]:
                    t.processIrTemp(message)
                    break
        elif message["content"] == "gyro":
            for g in self.gyro:
                if g.id == self.idToName[message["id"]]:
                    g.processGyro(message)
                    break
        elif message["content"] == "magnetometer":
            for g in self.magnet:
                if g.id == self.idToName[message["id"]]:
                    g.processMagnet(message)
                    break
        elif message["content"] == "buttons":
            for b in self.buttons:
                if b.id == self.idToName[message["id"]]:
                    b.processButtons(message)
                    break
        elif message["content"] == "rel_humidity":
            for b in self.humidity:
                if b.id == self.idToName[message["id"]]:
                    b.processHumidity(message)
                    break

    def onAdaptorFunctions(self, message):
        logging.debug("%s onAdaptorFunctions, message: %s", ModuleName, message)
        self.devServices.append(message)
        serviceReq = []
        for p in message["functions"]:
            # Based on services offered & whether we want to enable them
            if p["parameter"] == "temperature":
                if TEMP:
                    self.temp.append(TemperatureMeasure((self.idToName[message["id"]])))
                    self.temp[-1].dm = self.dm
                    serviceReq.append({"parameter": "temperature",
                                       "interval": SENSOR_POLLING_INTERVAL})
            elif p["parameter"] == "ir_temperature":
                if IRTEMP:
                    self.irTemp.append(IrTemperatureMeasure(self.idToName[message["id"]]))
                    self.irTemp[-1].dm = self.dm
                    serviceReq.append({"parameter": "ir_temperature",
                                       "interval": SENSOR_POLLING_INTERVAL})
            elif p["parameter"] == "acceleration":
                if ACCEL:
                    self.accel.append(Accelerometer((self.idToName[message["id"]])))
                    serviceReq.append({"parameter": "acceleration",
                                       "interval": SENSOR_POLLING_INTERVAL})
                    self.accel[-1].dm = self.dm
            elif p["parameter"] == "gyro":
                if GYRO:
                    self.gyro.append(Gyro(self.idToName[message["id"]]))
                    self.gyro[-1].dm = self.dm
                    serviceReq.append({"parameter": "gyro",
                                       "interval": SENSOR_POLLING_INTERVAL})
            elif p["parameter"] == "magnetometer":
                if MAGNET: 
                    self.magnet.append(Magnet(self.idToName[message["id"]]))
                    self.magnet[-1].dm = self.dm
                    serviceReq.append({"parameter": "magnetometer",
                                       "interval": SENSOR_POLLING_INTERVAL})
            elif p["parameter"] == "buttons":
                if BUTTONS:
                    self.buttons.append(Buttons(self.idToName[message["id"]]))
                    self.buttons[-1].dm = self.dm
                    serviceReq.append({"parameter": "buttons",
                                      "interval": 0})
            elif p["parameter"] == "rel_humidity":
                if HUMIDITY:
                    self.humidity.append(Humid(self.idToName[message["id"]]))
                    self.humidity[-1].dm = self.dm
                    serviceReq.append({"parameter": "rel_humidity",
                                      "interval": SENSOR_POLLING_INTERVAL})
        msg = {"id": self.id,
               "request": "functions",
               "functions": serviceReq}
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

    app = App(sys.argv)
