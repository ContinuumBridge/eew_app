#!/usr/bin/env python
# eew_app.py
# Copyright (C) ContinuumBridge Limited, 2014 - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# Written by Peter Claydon
#
ModuleName = "eew_app" 

# Enable required sensors
TEMP = True
IRTEMP = True
ACCEL = False
HUMIDITY = True
GYRO = False
MAGNET = False
BUTTONS = True

# Mininum change in parameters before it is reported
TEMP_MIN_CHANGE = 0.2
IRTEMP_MIN_CHANGE = 0.5
HUMIDITY_MIN_CHANGE = 0.5
ACCEL_MIN_CHANGE = 0.02
GYRO_MIN_CHANGE = 0.5
MAGNET_MIN_CHANGE = 0.5

import sys
import os.path
import time
import logging
from cbcommslib import CbApp
from cbconfig import *

class DataManager:
    """ Managers data storage for all sensors """
    def __init__(self, sendMessage):
        self.sendMessage = sendMessage
        self.now = self.niceTime(time.time())
        self.cvsList = []
        self.cvsLine = []
        self.index = []

    def niceTime(self, timeStamp):
        localtime = time.localtime(timeStamp)
        milliseconds = '%03d' % int((timeStamp - int(timeStamp)) * 1000)
        now = time.strftime('%Y:%m:%d,  %H:%M:%S:', localtime) + milliseconds
        return now

    def writeCVS(self, timeStamp):
        self.then = self.now
        self.now = self.niceTime(timeStamp)
        if self.now != self.then:
            self.f.write(self.then + ",")
            for i in range(len(self.cvsLine)):
                self.f.write(self.cvsLine[i] + ",")
                self.cvsLine[i] = ""
            self.f.write("\n")

    def initFile(self, idToName):
        self.idToName = idToName
        for i in self.idToName:
            self.index.append(self.idToName[i])
        services = ["temperature", 
                    "ir_temperature", 
                    "accel x", "accel y", "accel z",
                    "buttons l", "buttons r",
                    "rel humidily",
                    "pressure"]
        self.numberServices = len(services)
        for i in self.idToName:
            for s in services:
                self.cvsList.append(s)
                self.cvsLine.append("")
        fileName = CB_CONFIG_DIR + "eew_app.csv"
        if os.path.isfile(fileName):
            self.f = open(fileName, "a+", 0)
        else:
            self.f = open(fileName, "a+", 0)
            for d in self.idToName:
                self.f.write(d + ", " + self.idToName[d] + "\n")
            self.f.write("date, time, ")
            for i in self.cvsList:
                self.f.write(i + ", ")
            self.f.write("\n")

    def storeAccel(self, deviceID, timeStamp, a):
        self.writeCVS(timeStamp)
        index = self.index.index(deviceID)
        for i in range(3):
            self.cvsLine[index*self.numberServices + 2 + i] = str("%2.3f" %a[i])
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "timeStamp": timeStamp,
                        "type": "accel",
                        "data": a
                       }
              }
        self.sendMessage(req, "conc")

    def storeTemp(self, deviceID, timeStamp, temp):
        self.writeCVS(timeStamp)
        index = self.index.index(deviceID)
        self.cvsLine[index*self.numberServices + 0] = str("%2.1f" %temp)
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "type": "temperature",
                        "timeStamp": timeStamp,
                        "data": temp
                       }
              }
        self.sendMessage(req, "conc")

    def storeIrTemp(self, deviceID, timeStamp, temp):
        self.writeCVS(timeStamp)
        index = self.index.index(deviceID)
        self.cvsLine[index*self.numberServices + 1] = str("%2.1f" %temp)
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "type": "ir_temperature",
                        "timeStamp": timeStamp,
                        "data": temp
                       }
              }
        self.sendMessage(req, "conc")

    def storeHumidity(self, deviceID, timeStamp, h):
        self.writeCVS(timeStamp)
        index = self.index.index(deviceID)
        self.cvsLine[index*self.numberServices + 7] = str("%2.1f" %h)
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "type": "rel_humidity",
                        "timeStamp": timeStamp,
                        "data": h
                       }
              }
        self.sendMessage(req, "conc")


    def storeButtons(self, deviceID, timeStamp, buttons):
        self.writeCVS(timeStamp)
        index = self.index.index(deviceID)
        self.cvsLine[index*self.numberServices + 5] = str(buttons["leftButton"])
        self.cvsLine[index*self.numberServices + 6] = str(buttons["rightButton"])
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "type": "buttons",
                        "timeStamp": timeStamp,
                        "data": [buttons["leftButton"], buttons["rightButton"]]
                       }
              }
        self.sendMessage(req, "conc")

    def storeGyro(self, deviceID, timeStamp, gyro):
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "type": "gyro",
                        "timeStamp": timeStamp,
                        "data": gyro
                       }
              }
        self.sendMessage(req, "conc")

    def storeMagnet(self, deviceID, timeStamp, magnet):
        req = {
               "msg": "req",
               "verb": "post",
               "channel": self.appNum,
               "body": {
                        "msg": "data",
                        "appID": self.appID,
                        "deviceID": deviceID,
                        "type": "magnetometer",
                        "timeStamp": timeStamp,
                        "data": magnet
                       }
              }
        self.sendMessage(req, "conc")

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
        self.dm = DataManager(self.sendMessage)
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
        #logging.debug("%s onAdaptorFunctions, message: %s", ModuleName, message)
        self.devServices.append(message)
        serviceReq = []
        for p in message["functions"]:
            # Based on services offered & whether we want to enable them
            if p["parameter"] == "temperature":
                if TEMP:
                    self.temp.append(TemperatureMeasure((self.idToName[message["id"]])))
                    self.temp[-1].dm = self.dm
                    serviceReq.append("temperature")
            elif p["parameter"] == "ir_temperature":
                if IRTEMP:
                    self.irTemp.append(IrTemperatureMeasure(self.idToName[message["id"]]))
                    self.irTemp[-1].dm = self.dm
                    serviceReq.append("ir_temperature")
            elif p["parameter"] == "acceleration":
                if ACCEL:
                    self.accel.append(Accelerometer(self.idToName(message["id"])))
                    serviceReq.append("acceleration")
                    self.accel[-1].dm = self.dm
            elif p["parameter"] == "gyro":
                if GYRO:
                    self.gyro.append(Gyro(self.idToName[message["id"]]))
                    self.gyro[-1].dm = self.dm
                    serviceReq.append("gyro")
            elif p["parameter"] == "magnetometer":
                if MAGNET: 
                    self.magnet.append(Magnet(self.idToName[message["id"]]))
                    self.magnet[-1].dm = self.dm
                    serviceReq.append("magnetometer")
            elif p["parameter"] == "buttons":
                if BUTTONS:
                    self.buttons.append(Buttons(self.idToName[message["id"]]))
                    self.buttons[-1].dm = self.dm
                    serviceReq.append("buttons")
            elif p["parameter"] == "rel_humidity":
                if HUMIDITY:
                    self.humidity.append(Humid(self.idToName[message["id"]]))
                    self.humidity[-1].dm = self.dm
                    serviceReq.append("rel_humidity")
        msg = {"id": self.id,
               "request": "functions",
               "functions": serviceReq}
        self.sendMessage(msg, message["id"])
        self.setState("running")

    def onConfigureMessage(self, config):
        """ Config is based on what sensors are available """
        self.dm.appID = self.id
        self.dm.appNum = int(self.id[3:])
        for adaptor in config["adaptors"]:
            adtID = adaptor["id"]
            if adtID not in self.devices:
                # Because configure may be re-called if devices are added
                name = adaptor["name"]
                friendly_name = adaptor["friendly_name"]
                logging.debug("%s Configure app. Adaptor name: %s", ModuleName, name)
                self.idToName[adtID] = friendly_name.replace(" ", "_")
                self.devices.append(adtID)
        self.dm.initFile(self.idToName)
        self.setState("starting")

if __name__ == '__main__':

    app = App(sys.argv)
