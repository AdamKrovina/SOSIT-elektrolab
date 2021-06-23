import pyvisa

import enum
class Impedance(enum.Enum):
    HighZ = 0
    FiftyOhm = 1

#need a way to handle error/timeout on query

#Function generator class
class MSO5000Gen(object):
    def __init__(self):
        pass
    def setOffset(self):
        pass

#Oscilloscope class
class MSO5000(object):
    def __init__(self):
        pass

    def findDevs(self):
        rm = pyvisa.ResourceManager()
        res = None
        res = rm.list_resources()
        res += ('COM3',)
        return res

    #Place your Serial number here
    def conn(self, constr="USB0::0x1AB1::0x0643::DG8XXXXXXXXXX::INSTR"):
        """Attempt to connect to instrument"""
        rm = pyvisa.ResourceManager()
        self.inst = rm.open_resource(constr)

    def identify(self):
        """Return identify string which has serial number"""
        return self.inst.query("*IDN?")

    def getPNG(self):
        #self.inst.write(':HCOP:SDUM:DATA:FORM PNG')
        #bmpdata = self.inst.query(':display:data?')       #returns screenshot in BMP format
        #       bmpdata = self.inst.read_raw(391734+11)
        #bmpdata = bmpdata[11:]
        bmpdata = 0  #scpi screenshot command not working
        return bmpdata

    #DG800 screen resolution = 480x272 = 130560
    #MSO5000 resolution = 1024x768 = 786432

    def querying(self, command="*IDN?"):
        resp = self.inst.query(command)
        return resp.rstrip()

    def dis(self):
        del self.inst

    def writing(self, command=""):
        self.inst.write(command)

#TEMPORARY, move everything to functions
    def write(self, command=""):
            self.inst.write(command)

    def query(self, command="*IDN?"):
        try:
            resp = self.inst.query(command)
            return resp.rstrip()
        except:
            return 0

#Function generator
    def setFrequency(self, freq=1000.0, channel=1):
        if self.checkChannelValid(channel):
            self.inst.write(':source' + str(channel) + ':freq ' + str(freq))

    def setPhase(self, phase=0.0, channel=1):
        if self.checkChannelValid(channel):
            self.inst.write(':source' + str(channel) + ':phase ' + str(phase))

    def alignPhase(self, channel=1):
        if self.checkChannelValid(channel):
            self.inst.write(':source' + str(channel) + ':phase:init')

    def setFunction(self, func="sin", channel=1):
        if self.checkChannelValid(channel):
            self.inst.write(':source' + str(channel) + ':function ' + func)
        #if sin/square

    def setVoltage(self, volt=1.0, channel=1):
        if self.checkChannelValid(channel):
            valid = {10, 90}
            self.inst.write(':source' + str(channel) + ':volt ' + str(volt))

    #10-90% duty cycle
    def setDutyCycle(self, duty=50.0, channel=1):
        if self.checkChannelValid(channel):
            self.inst.write(':source' + str(channel) + ':pulse:dcycle ' + str(duty))

    def setModulation(self, channel=1):
        pass

    def setOffset(self, volt=0.0, channel=1):
        if self.checkChannelValid(channel):
            self.inst.write(':source' + str(channel) + ':voltage:offset 0')

    def setOutput(self, state=True, channel=1):
        if self.checkChannelValid(channel):
            if state:
                self.inst.write(':source' + str(channel) + ':output ON')
            else:
                self.inst.write(':source' + str(channel) + ':output OFF')

    def setImpedance(self, imp=Impedance.HighZ, channel=1):
        if self.checkChannelValid(channel):
            if imp == Impedance.HighZ:
                self.inst.writing("source:outp' + str(channel) + ':IMP omeg")
            if imp == Impedance.FiftyOhm:
                self.inst.writing("source:outp' + str(channel) + ':IMP fifty")

    def setAcquisitionType(self, type='normal', num_avg=8):
        valid = {'normal', 'averages', 'peak'}
        self.inst.write(':acquire:type ' + type)
        if type == 'averages':
            if (num_avg >= 2) & (num_avg <= 65536):
                self.inst.write(':acquire:averages ' + str(num_avg))
            else:
                ValueError

    #anti-alias, who knows what it does?

    def setMemoryDepth(self, depth='auto'):
        valid = {'auto', '1k', '10k', '100k', '1m', '10m', '25m', '50m', '100m', '200m'}
        self.inst.write(':acquire:mdepth ' + depth)

    def setChannelScale(self, scale="1.000", channel=1):
        self.inst.write(':channel' + str(channel) + ':scale ' + str(scale))

#Channel settings
    def setChannelOptions(self, BWlimit='OFF', coupling='DC', channel=1):
        validBW = {'20M', '100M', '200M', 'OFF'}
        self.inst.write(':channel' + str(channel) + ':bwlimit ' + BWlimit)

        validCouple = {'AC', 'DC'}
        self.inst.write(':channel' + str(channel) + ':coupling ' + coupling)



#Timebase
    #modes Main, Xy, Roll
    def setTimebaseMode(self, mode='main'):
        self.inst.write(':timebase:mode ' + mode)

    #modes: center, lb, rb, trig, user
    def setTimebasePosition(self, ref='center'):
        self.inst.write(':timebase:hreference:mode ' + ref)

    def setTimebase(self, timebase=0.001):
        self.inst.write(':timebase:main:scale ' + str(timebase))  #f'{numvar:.9f}'

#Trigger
    #mode: edge, pulse, slope, video, pattern, duration, timeout, runt, window, delay, setup, nedge, ...
    #coupling: ac, dc, lfreject, hfreject
    #sweep: auto, normal, single
    #holdoff:
    #source: channel1, channel2, D0, etc..
    def setTrigger(self, mode='edge', coupling='ac', sweep='normal', slope='positive', level=0.00, source='channel1'):
        self.inst.write(':trigger:mode ' + mode)
        self.inst.write(':trigger:coupling ' + coupling)
        self.inst.write(':trigger:sweep ' + sweep)
        self.inst.write(':trigger:source ' + source)
        self.inst.write(':trigger:slope ' + slope)
        self.inst.write(':trigger:level ' + str(level))

#display
    def displayClear(self):
        self.inst.write(':display:clear')

#read values
    def getMeasAmplitude(self, channel=1):
        try:
            return float(self.inst.query(':measure:item? vamp,channel' + str(channel)).rstrip())  #request measurement, convert to float
        except:
            return 0

    def getMeasFrequency(self, channel=1):
        try:
            return float(self.inst.query(':measure:item? freq,channel' + str(channel)).rstrip())
        except:
            return 0

    def getImpedance(self, channel=1):
        #if string == "OMEG" or "FIFT"
        return Impedance.FiftyOhm

    def setupMeasPhase(self, channelA=1, channelB=2):       #can also use digital or math channels
        self.inst.write(':measure:setup:psa chan' + str(channelA))
        self.inst.write(':measure:setup:psb chan' + str(channelB))
        #self.inst.write(':measure:setup:dsa chan' + str(channelA))
        #self.inst.write(':measure:setup:dsb chan' + str(channelB))

    def getMeasPhase(self, channelA=1, channelB=2):
        return float(self.inst.query(
            ':measure:item? rrphase,channel' + str(channelA) + ',channel' + str(channelB)).rstrip())  #request measurement, convert to float
        #rrPhase, rfPhase frphase ffphase? which one

    def getOutputState(self, channel="1"):
        resp = self.inst.query(":source:OUTP" + str(channel) + ":state?")
        resp = resp.rstrip()
        if resp == "1":
            return True
        if resp == "0":
            return False
        else:
            return ValueError

#Read waveform data
    #set waveform source channel
    def waveSource(self, channel='channel1'):
        self.checkSourceValid(channel)
        self.inst.write(':waveform:source ' + channel)

    #mode: normal, maximum, raw (must be in stop mode)
    #format: word, byte, ascii (comma separated scientific notation)
    def waveDataFormat(self, mode='normal', format='byte', points=1000):
        self.inst.write(':waveform:mode ' + mode)
        self.inst.write(':waveform:format ' + format)
        self.inst.write(':waveform:format ' + str(points))

    def getWaveData(self):

        pass

#something to differentiate the gen from the scope
    #eg scope.setOffset
    #gen.setOffset


    #validation
    def checkChannelValid(self, channel):
        if (channel == 1) | (channel == 2):
            return True
        else:
            return False

    def checkSourceValid(self, source):
        valid = {'channel1', 'channel2', 'channel3', 'channel4',
                 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'd10', 'd11', 'd12', 'd13', 'd14', 'd15',
                 'math1', 'math2', 'math3', 'math4'}
        source = source.lower()
        if source in valid:
            pass
        else:
             ValueError

    def checkScopeChannel(self, channel):
        return True


if __name__ == '__main__':
    test = MSO5000()

    devs = test.findDevs()
    for device in devs:
        if ("USB" in device):
            print(device)
        print(device)
    print(devs)

    test.conn(devs[0])
    print (test.identify())
    
    # function generator setup
    # test.setFrequency(freq=50, channel=1)
    # test.setFunction(func='RAMP')
    
    # print('Setting 1: ', test.query(':WAVeform:CHANnel:SOURce CHANnel1'))
    # print('Setting 2: ', test.query(':WAVeform:MODE RAW'))
    # print('Setting 3: ', test.query(':WAVeform:FORMat ASCii'))
    # print('Setting 4: ', test.query(':WAVeform:POINts 10000'))
    # print('Setting 4: ', test.query(':WAVeform:DATA?'))
    
    
    # test.write(command=':WAVeform:CHANnel:SOURce CHANnel1')
    # test.write(command=':WAVeform:MODE RAW')
    # test.write(command=':WAVeform:FORMat ASCii')
    # test.write(command=':WAVeform:POINts 10000')
    # data = test.query(':WAVeform:DATA?')
    
    
    # import pandas as pd
    # import matplotlib.pyplot as plt
    # import numpy as np


    # fig = plt.figure('Stat')
    # plt.plot(data)





















