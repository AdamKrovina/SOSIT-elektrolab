# -*- coding: utf-8 -*-
"""
Created on Sun Dec  6 14:50:42 2020

@author: Adam Krovina
"""

from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import time
import pyvisa as visa
import numpy as np

enableVisa = True

ard01ena = True # arduino 2 enable

if enableVisa:
    rm = visa.ResourceManager()
    devs_found = rm.list_resources()
    #instr = rm.open_resource('ASRL3::INSTR')
    #instr = rm.open_resource(devs_found[0])
    #instr2 = rm.open_resource(devs_found[1])
    
    print('Waiting for home')
    for i in range(2):
        time.sleep(1)
        print('.', end='')
    print()
    
    for dev in devs_found:
        try:
            instrument = rm.open_resource(dev)
        except:
            continue
        time.sleep(3)
        instrument.write('\n')
        time.sleep(0.1)
        while instrument.bytes_in_buffer > 0:
            instrument.read()
            time.sleep(0.1)
        sn = instrument.query('*IDN?\n')
        print(sn)
        if 'TENMA 72-2540 V5.2 SN:10830844' in sn:
            zdroj = instrument
        if 'Vrekrer,Arduino SCPI Dimmer,#00,v0.4' in sn:
            arduino = instrument
        if 'Vrekrer,Arduino SCPI Dimmer,#01,v0.4' in sn:
            arduino01 = instrument


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SPREADSHEET_ID = '1WQCET_f_vg7fs-7Wr4CdIJ6uKHaXaWVGRLNfV7xSv5M'
InputRange = 'Meranie!B6:Q10'
OutputRange = 'Meranie!R6:S10'
LimitsRange = 'Rozsahy!A3:H6'
TriggerRange = 'Meranie!B3'

"""Shows basic usage of the Sheets API.
Prints values from a sample spreadsheet.
"""
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

while True:
    #### Zistenie zmeny Trigger policka 
    TriggerinputValues = []
    
    while not TriggerinputValues:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=TriggerRange).execute()
        TriggerinputValues = result.get('values', [])
        time.sleep(5)
    
    #### Vynulovanie Trigger policka
    TriggerinputValues[0][0] = 'Prebieha meranie...'
    body = {
        'values': TriggerinputValues
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=TriggerRange,
        valueInputOption='RAW', body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))

    ### Vycitanie Rozsahov
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=LimitsRange).execute()
    LimVals = result.get('values', [])
    
    ### Vycitanie Vstupnych dat
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=InputRange).execute()
    inputValues = result.get('values', [])
    
    
    # if not values:
    #     print('No data found.')
    # else:
    #     for row in values:
    #         # Print columns A and E, which correspond to indices 0 and 4.
    #         print('%s, %s' % (row[0], row[4]))
    
    for i in range(len(inputValues)): #riadky
        for j in range(len(inputValues[i])): #stlpce
            print(str(inputValues[i][j]) + ', ', end='')
        print('')
        
        
    zdrojUMax = 30
    zdrojIlimitMax = 0.3
    zdrojIlimitDefault = 0.3    
    pot1Min = 0
    pot1Max = 6300
    pot2Min = 0
    pot2Max = 6300
    
    OutputValues = []
    
    if enableVisa:
        zdroj.write('VSET1:0\n')
        zdroj.write('OUT1')
    
    def clamp(n, smallest, largest): return max(smallest, min(n, largest))
    
    for i in range(len(inputValues)): #riadky
         try:
            rel1 = clamp(int(inputValues[i][4]), 0, 1)
            rel2 = clamp(int(inputValues[i][5]), 0, 1)           
            rel3 = clamp(int(inputValues[i][6]), 0, 1)
            rel4 = clamp(int(inputValues[i][7]), 0, 1) 
            rel5 = clamp(int(inputValues[i][8]), 0, 1) 
            rel6 = clamp(int(inputValues[i][9]), 0, 1) 
            rel7 = clamp(int(inputValues[i][10]), 0, 1) 
            rel8 = clamp(int(inputValues[i][11]), 0, 1) 
            rel9 = clamp(int(inputValues[i][12]), 0, 1) 
            rel10 = clamp(int(inputValues[i][13]), 0, 1) 
            rel11 = clamp(int(inputValues[i][14]), 0, 1) 
            rel12 = clamp(int(inputValues[i][15]), 0, 1) 

            LimIdx = rel1 + rel2*2 # Vypocet indexu dvojkoveho
            U = clamp(float(inputValues[i][0]), 0, float(LimVals[LimIdx][2]))
            Ilim = clamp(float(inputValues[i][1]), 0, float(LimVals[LimIdx][3]))
            pot1 = clamp(int(inputValues[i][2]), int(LimVals[LimIdx][4]), int(LimVals[LimIdx][5]))
            pot2 = clamp(int(inputValues[i][3]), int(LimVals[LimIdx][6]), int(LimVals[LimIdx][7]))
            
            print('LimIdx: ' + str(LimIdx) + ' U: ' + str(U) + ' Ilim: ' + str(Ilim) + ' pot1: ' + str(pot1) + ' pot2: ' + str(pot2))
            
            if enableVisa: 
                if pot1Min <= pot1 <= pot1Max:
                    arduino.write('mot 1,' + str(pot1))
                    time.sleep(0.1)
                if pot1Min <= pot2 <= pot1Max:
                    arduino.write('mot 2,' + str(pot2))
                    time.sleep(0.1)
                arduino.write('rel 1,' + str(rel1))
                time.sleep(0.1)
                arduino.write('rel 2,' + str(rel2))
                if ard01ena: 
                    if rel3 == 1:
                        arduino01.write('rel 1,' + str(rel3) + ',1800') # casove obmedzenie v *0,1 s
                    else: arduino01.write('rel 1,' + str(rel3))
                time.sleep(0.1)
                if ard01ena: 
                    if rel4 == 1:
                        arduino01.write('rel 2,' + str(rel4) + ',1800') # casove obmedzenie v *0,1 s
                    else: arduino01.write('rel 2,' + str(rel4))
                
                if not 0 <= Ilim <= zdrojIlimitMax:
                    Ilim = 0;
                zdroj.write('ISET1:' + str(Ilim) + '\n')
                if not 0 <= U <= zdrojUMax:
                    U = 0;
                zdroj.write('VSET1:' + str(U) + '\n')

                time.sleep(3)
                napatie = float(zdroj.query('VOUT1?\n'))
                time.sleep(0.1)
                prud = 1000*float(zdroj.query('IOUT1?\n'))
                OutputValues.append([napatie,prud])
         except:
            OutputValues.append(['chyba', 'chyba'])
    
    if enableVisa:                
        zdroj.write('VSET1:0\n')
        zdroj.write('OUT0')
        
    body = {
        'values': OutputValues
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=OutputRange,
        valueInputOption='RAW', body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))
    
    #### Vynulovanie Trigger policka
    TriggerinputValues = [['']]
    body = {
        'values': TriggerinputValues
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range=TriggerRange,
        valueInputOption='RAW', body=body).execute()
    print('{0} cells updated.'.format(result.get('updatedCells')))