import csv
import signal
import sys
import telnetlib
import time

import pandas as pd
import numpy as np
import pyvisa
import serial


data_log = []

#sets chan 3 to voltage source mode, sets voltage, and turns on
def v_source(v_lim):
    v_lim = str(v_lim)
    N6705C.write("SOURce:EMUlation PS1Q, (@3)")
    N6705C.write("VOLT " + v_lim + ",(@3)")
    #N6705C.write("CURR:LIM " + i_lim + ",(@1)")#make variable user input
    N6705C.write("OUTP ON,(@3)")

#sets up Keysight to emulate battery charger
# @param voltage limit and current limit.
def charge_mode(v_lim, i_lim, N6705C):
    v_lim = str(v_lim)``
    i_lim = str(i_lim)
    N6705C.write("SOURce:EMUlation CHARger, (@3)")
    N6705C.write("VOLT " + v_lim + ",(@3)")
    N6705C.write("CURR:LIM " + i_lim + ",(@3)")#make variable user input
    N6705C.write("OUTP ON,(@3)")

#sets up CC LoadCC Load
def CCLoad_mode(v_lim, i_lim, N6705C):
    v_lim = str(v_lim)
    i_lim = str(i_lim)
    N6705C.write("SOURce:EMUlation CCLoad, (@3)")
    N6705C.write("CURR:LIM " + i_lim + ",(@3)")#make variable user input
    N6705C.write("OUTP ON,(@3)")

def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    f.close()
    sys.exit(0)

def rtt_cmd(cmd):
    cmd = cmd + "\r\n"
    cmd = cmd.encode('utf-8')
    HOST = "localhost"
    PORT = "19021"
    tn = telnetlib.Telnet(HOST,PORT,5)
    tn.write(cmd)
    time.sleep(1)
    data = tn.read_until(b"compat>")
    data = data.decode('ascii')
    data = data.split('mfg')[-1].split('SUCCESS')[0]
    data = "".join(data.splitlines())
    if(b"read" in cmd):
        data = data.split('VAL, ')[-1][:-7]
        data = float(data)/100
    if data != '':
        print(data)
        #f.write(data.decode('ascii'))
        return data

def main():


    # arr = np.array([[1, 2, 3,4], [4, 5, 6,44], [7, 8, 9,44]])
    # dataframe


    #set up telnet connection
    signal.signal(signal.SIGINT, signal_handler)
    HOST = "localhost"
    PORT = "19021"
    tn = telnetlib.Telnet(HOST,PORT,5)
    rm = pyvisa.ResourceManager()
    print(str(rm))
    print(rm.list_resources())
    N6705C = rm.open_resource('USB0::0x2A8D::0x0F02::MY56000941::0::INSTR')
    N6705C.write("*CLS")
    print(N6705C.query('*IDN?'))

    voltage = float(N6705C.query('MEASure:VOLTage? (@3)'))
    # this should start the charging.
    # if(voltage < 4.35):
    #     print("Charging Battery")
    #     start_time = time.perf_counter()
    #     charge_mode(4.35, 0.355, N6705C)
    # else:
    #     print("Draining Battery")
    #     start_time = time.perf_counter()
    #     CCLoad_mode(4.35, (0.355*2), N6705C)

    voltage = float(N6705C.query('MEASure:VOLTage? (@3)'))
    current = float(N6705C.query('MEASure:CURRent? (@3)'))

    arr = np.empty(shape=[0, 4])

    while(voltage < 4.35 and current > 0.0071):
        print("Charging Battery")
        start_time = time.perf_counter()
        charge_mode(4.35, 0.355, N6705C)
        voltage = float(N6705C.query('MEASure:VOLTage? (@3)'))
        current = float(N6705C.query('MEASure:CURRent? (@3)'))
        elapsed_time = time.perf_counter() - start_time
        #make this using pandas dataframe ? add the RTT command readings for mfg 
        expected_capacity = rtt_cmd("mfg fuel soc") #this should obtain value from machine
        actual_capacity = (elapsed_time * expected_capacity)
        data_log.append([elapsed_time, voltage, current, expected_capacity, actual_capacity])
        print(data_log)

        row = np.array([elapsed_time, voltage, current, expected_capacity, actual_capacity])
        arr = np.vstack([arr,row])
        print(data_log)

        time.sleep(2)
    
        df2 = pd.DataFrame(arr,columns=['Elapsed Time', 'V', 'I', "Exp_Cap", "Act_Cap"])
        print(df2)

    while(voltage >= 4.35 and current < 0.0071):
        print("Draining Battery")
        start_time = time.perf_counter()
        CCLoad_mode(4.35, (0.355*2), N6705C)
        voltage = float(N6705C.query('MEASure:VOLTage? (@3)'))
        current = float(N6705C.query('MEASure:CURRent? (@3)'))
        elapsed_time = time.perf_counter() - start_time
        #make this using pandas dataframe ? add the RTT command readings for mfg 
        expected_capacity = rtt_cmd("mfg fuel soc") #this should obtain value from machine
        actual_capacity = (elapsed_time * expected_capacity)
        data_log.append([elapsed_time, voltage, current, expected_capacity, actual_capacity])
        print(data_log)

        row = np.array([elapsed_time, voltage, current, expected_capacity, actual_capacity])
        arr = np.vstack([arr,row])
        print(data_log)

        time.sleep(2)
    
        df2 = pd.DataFrame(arr,columns=['Elapsed Time', 'V', 'I', "Exp_Cap", "Act_Cap"])
        print(df2)

    #N6705C.write("OUTP OFF,(@3)")

#mfg fuel soc save every two seconds to an array

if __name__=="__main__":
    main()