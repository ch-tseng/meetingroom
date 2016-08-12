#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import RPi.GPIO as GPIO
import requests
import mcp3008
import time
import json
import Adafruit_DHT as dht
import random
from subprocess import call

#========================================================

meetroom = "亞歷山大"
speak = 0
pirDelay = 300  # seconds
defaultVolume = 750


#========================================================


pinDHT22 = 13  # GPIO 13
pinPIR = 35
pinLED_RED = 38
pinLED_BLUE = 36
pinLED_YELLOW = 40

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(pinPIR, GPIO.IN)
GPIO.setup(pinLED_RED, GPIO.OUT)
GPIO.setup(pinLED_YELLOW, GPIO.OUT)
GPIO.setup(pinLED_BLUE, GPIO.OUT)

#======================================================================
lastPIRdetect = time.time()
ledMode = 0  # LED status now
sensorHumdity = 0
sensorTemperture = 0
sensorLight_r = 0
sensorLight_l = 0
sensorLight_c = 0
sensorSound = 0
nowHour = 0
pirValueNow = 0  # 目前PIR sensor的值
welcomeMSG = ["wav/welcome1.mp3", "wav/welcome2.mp3",
              "wav/welcome3.mp3", "wav/welcome4.mp3"]
sensorTemperture = 0
sensorHumdity = 0

#===Functions===========================================================


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except:
        return False
    return True


def playAudio(volumn, audioFile):
    global ledMode

    lightLED(5)
    print("Play audio --> " + audioFile)
    if speak==1:
        call(["omxplayer", "--no-osd", "--vol", str(volumn), "--no-osd", audioFile])

    lightLED(ledMode)


def speakNumber(volumn, numSpeak):
    if numSpeak > 100:
        strNum = str(numSpeak)
        for i in range(0, len(strNum)):
            playAudio(volumn, "wav/number/" + strNum[i] + ".mp3")

    else:
        playAudio(volumn, "wav/number/" + str(numSpeak) + ".mp3")


def lightLED(mode):
    if mode == 0:  # 不亮
        GPIO.output(pinLED_BLUE, GPIO.LOW)
        GPIO.output(pinLED_RED, GPIO.LOW)
        GPIO.output(pinLED_YELLOW, GPIO.LOW)
    elif mode == 1:  # RED, 會議室有人
        GPIO.output(pinLED_BLUE, GPIO.LOW)
        GPIO.output(pinLED_RED, GPIO.HIGH)
        GPIO.output(pinLED_YELLOW, GPIO.LOW)
    elif mode == 2:  # 會議室無人
        GPIO.output(pinLED_BLUE, GPIO.LOW)
        GPIO.output(pinLED_RED, GPIO.LOW)
        GPIO.output(pinLED_YELLOW, GPIO.LOW)
    elif mode == 5:  # speaking
        GPIO.output(pinLED_BLUE, GPIO.HIGH)
        GPIO.output(pinLED_RED, GPIO.LOW)
        GPIO.output(pinLED_YELLOW, GPIO.HIGH)
    else:
        GPIO.output(pinLED_BLUE, GPIO.LOW)
        GPIO.output(pinLED_RED, GPIO.LOW)
        GPIO.output(pinLED_YELLOW, GPIO.LOW)


def convertTime(stringTime):
    hour = int(stringTime[:2])
    min = int(stringTime[3:5])
    if stringTime[-2:] == "PM":
        hour = hour + 12

    print("Hour:" + str(hour) + " / Min:" + str(min))


def welcome():
    audioFile = random.choice(welcomeMSG)
    playAudio(defaultVolume, audioFile)


def envStatus():
    global sensorTemperture, sensorHumdity

    playAudio(defaultVolume, "wav/TemperatureNow.mp3")
    speakNumber(defaultVolume, sensorTemperture)
    playAudio(defaultVolume, "wav/degreeC_andHumandity.mp3")
    speakNumber(defaultVolume, sensorHumdity)
    playAudio(defaultVolume, "wav/percent.mp3")

    if sensorTemperture >= 30:
        playAudio(defaultVolume, "wav/feelhot.mp3")


def getBookStatus():
    global nowHour, defaultVolume

    r = requests.get(
        #        'http://data.sunplusit.com/Api/Meetingroom?code=7EE75E3E74A555A0482578ED00223AEF&room=%E8%8E%8E%E5%A3%AB%E6%AF%94%E4%BA%9E')
        'http://data.sunplusit.com/Api/Meetingroom?code=7EE75E3E74A555A0482578ED00223AEF&room=' + meetroom)
    if is_json(r.text):
        jsonData = json.loads(r.text)
        if len(jsonData) > 0:
            playAudio(defaultVolume, "wav/TodayHave.mp3")
            playAudio(defaultVolume, "wav/number/" +
                      str(len(jsonData)) + ".mp3")
            playAudio(defaultVolume, "wav/RecordsBooked.mp3")
            #---最近的一筆預約
            minHour = 24
            minIndex = 0  # 最近的那筆預約編號
            print("jsonData length = " + str(len(jsonData)))
            for x in range(len(jsonData)):
                startTime = jsonData[x]["StartTime"]
                #startTime = jsonData[x]["EndTime"]

                hour = int(startTime[:2])
                min = int(startTime[3:5])
                if startTime[-2:] == "PM":
                    hour = hour + 12

                print("hour=" + str(hour) + " / nowHour=" + str(nowHour) + " / minHour=" + str(minHour) + " / X=" +
                      str(x))

                if hour - nowHour < minHour and hour - nowHour >= 0:
                    minIndex = x
                    minHour = hour - nowHour
                    meetingHour = hour
                    meetingMin = min
                    print("meetingHour=" + str(meetingHour))
                    print("meetingMin=" + str(meetingMin))

            if minHour == 24 and len(jsonData) > 0:
                print("No one book later....")
                # 到下班前都沒有人預約
                playAudio(defaultVolume, "wav/fromNowOnIsIdle.mp3")
            else:
                print("Next meeting index ID: " + str(minIndex))

                if minHour<=1:
                    if minHour == 0:
                        playAudio(defaultVolume, "wav/atNow.mp3")  # 目前
                    else:
                        playAudio(defaultVolume, "wav/waitAsecond.mp3")  # 待會
                else:
                    if minHour>2:
                        playAudio(defaultVolume, "wav/lastBootingTime.mp3")  # 
                    else:
                        playAudio(defaultVolume, "wav/later.mp3")  # 稍後

                if meetingMin > 0:
                    #playAudio(defaultVolume, "wav/number/" + str(meetingHour) + ".mp3")
                    speakNumber(defaultVolume, meetingHour)
                    playAudio(defaultVolume, "wav/point.mp3")  # 點
                    #playAudio(defaultVolume, "wav/number/" + str(meetingMin) + ".mp3")
                    speakNumber(defaultVolume, meetingMin)
                    playAudio(defaultVolume, "wav/minute.mp3")  # 分
                else:
                    playAudio(defaultVolume, "wav/number/" +
                              str(meetingHour) + ".mp3")
                    playAudio(defaultVolume, "wav/oclock.mp3")  # 點整

                #playAudio(defaultVolume, "wav/atThatTime.mp3")
                playAudio(defaultVolume, "wav/SomeOneBookTheMeeting.mp3")

        else:
            if nowHour <= 15:
                playAudio(defaultVolume, "wav/noOneBookToday.mp3")
            else:
                playAudio(defaultVolume, "wav/noOneBookAllDayToday.mp3")

# for Interrupts--------------------------


def MOTION(pinPIR):
    global ledMode, lastPIRdetect, pirDelay

    if (time.time() - lastPIRdetect) > pirDelay:
        print("Say welcome!")
        welcome()
        envStatus()

        getBookStatus()

    lastPIRdetect = time.time()
    if ledMode != 1:
        ledMode = 1
        lightLED(ledMode)

# Register----------------------------------------------
GPIO.add_event_detect(pinPIR, GPIO.RISING, callback=MOTION)

# playAudio(500, "wav/welcome_use.mp3")
# playAudio(1400, "wav/welcome_use.mp3")
#welcome()
#envStatus()
#getBookStatus()

try:
    while True:

        pirValueNow = GPIO.input(pinPIR)

        dt = list(time.localtime())
        nowYear = dt[0]
        nowMonth = dt[1]
        nowDay = dt[2]
        nowHour = dt[3]
        nowMinute = dt[4]

        sensorHumdity, sensorTemperture = dht.read_retry(dht.DHT22, pinDHT22)
        sensorHumdity = int(sensorHumdity)
        sensorTemperture = int(sensorTemperture)

        adc = mcp3008.MCP3008()
        tmpValue = adc.read([mcp3008.CH0])
        sensorLight_r = tmpValue[0]
        tmpValue = adc.read([mcp3008.CH1])
        sensorLight_l = tmpValue[0]
        tmpValue = adc.read([mcp3008.CH2])
        sensorLight_c = tmpValue[0]
        tmpValue = adc.read([mcp3008.CH3])
        sensorSound = tmpValue[0]
        adc.close()

        # 如果已經超過PIR delay時間
        secondsWait = time.time() - lastPIRdetect
        if secondsWait > pirDelay:
            # 但是PIR偵測到有人
            if pirValueNow == 1:
                lastPIRdetect = time.time()
                print("Still have people here.")
                if ledMode != 1:
                    ledMode = 1
                    lightLED(ledMode)
            else:
                if ledMode != 2:
                    print("No people here now.")
                    ledMode = 2
                    lightLED(ledMode)

        if pirValueNow == 1:
            lightLED(1)
        else:
            lightLED(2)

        print(str(int(pirDelay - secondsWait)) + ") Mode:" + str(ledMode) + " / PIR:" + str(pirValueNow) + " / T:" + str(sensorTemperture) +
              " / H:" + str(sensorHumdity) + " / S:" + str(sensorSound) + " / L_r:" + str(sensorLight_r) + " / L_c:" + str(sensorLight_c) + " / L_l:" + str(sensorLight_l))
        #time.sleep(5)

except:
    print("Unexpected error:", sys.exc_info()[0])
    raise
