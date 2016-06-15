# Copyright (c) 2016 Anastassios Martakos
# Created by: Anastassios Martakos

#!/usr/bin/env python3.4

import subprocess
from syslog import syslog, LOG_INFO

from lib.utils import decodeUTF8
from time import sleep

def disconnectWiFi(interface, defaults):
    proc = subprocess.Popen(['killall', 'wpa_supplicant'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))

    print("disconnect")

    proc = subprocess.Popen(['dhclient', '-r', interface], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))

    # proc = subprocess.Popen(['iw', 'dev', interface, 'disconnect'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # proc.communicate()

    proc = subprocess.Popen(['ip', 'link', 'set', interface, 'down'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))

    confDefaultGW(defaults['interface'], defaults['gateway'])

def connectWiFi(ssid, interface, wpa, logdir):
    if(wpa):
        proc = subprocess.Popen('wpa_supplicant -i ' + interface + ' -c ' + '/etc/wpa_supplicant-' + ssid + '.conf  > ' + logdir + '/' + ssid + '.tmplog &', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    else:
        proc = subprocess.Popen('iw dev ' + interface + ' connect -w ' + ssid + ' > ' + logdir + '/' + ssid + '.tmplog &' , stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

def initializeInterface(interface):
    proc = subprocess.Popen(['ip', 'link', 'set',  interface, 'up' ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))
    sleep(4)
    proc = subprocess.Popen(['iw', 'dev',  interface, 'scan' ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))

def getIP(interface):
    proc = subprocess.Popen(['dhclient', interface], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.pid

def killPID(pid):
    proc = subprocess.Popen(['kill', '-9',  str(pid)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))

def checkIP(gw):
    proc = subprocess.Popen(['ip', 'a'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()
    out = decodeUTF8(out)
    syslog(LOG_INFO, out)
    if ''.join(['inet ', gw[0:4]]) in out:
        return True
    else:
        return False

def checkConnection(interface, log):
    try:
        file = open(log, 'r')
        content = file.read()
        file.close()
    except:
        return False

    if 'connected to' in content:
        return True
    else:
        return False

    # proc = subprocess.Popen(['iw', 'dev', interface, 'link'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # out = proc.communicate()
    # out = decodeUTF8(out)
    # syslog(LOG_INFO, out)
    # if 'Not connected' in out:
    #     return False
    # else:
    #     return True

def checkAuth(interface, log):
    file = open(log, 'r')
    content = file.read()
    file.close()
    if 'Authentication succeeded' in content:
        return True
    else:
        return False

def doPingAvr(target, interface, count):
    proc = subprocess.Popen(['ping', ''.join(['-c', str(count)]), '-I', interface, target], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()
    out = decodeUTF8(out)
    syslog(LOG_INFO, out)

    try:
        out = out.split(' = ')[1]
        out = out.split(' ms')[0]
        out = out.split('/')[1]
    except:
        return 0

    return out

def getDBM(interface):
    proc = subprocess.Popen(['iw', 'dev', interface, 'link'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()
    out = decodeUTF8(out)
    syslog(LOG_INFO, out)
    try:
        out = out.split('signal: ')[1]
        out = out.split(' dBm')[0]
    except:
        return 'NULL'

    return out

def getBSSID(interface):
    proc = subprocess.Popen(['iw', 'dev', interface, 'link'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()
    out = decodeUTF8(out)
    syslog(LOG_INFO, out)
    try:
        out = out.split('Connected to ')[1]
        out = out.split(' (on ')[0]
    except IndexError as e:
        syslog(LOG_INFO, e.value)

    return out

def confDefaultGW(interface, gw):
    proc = subprocess.Popen(['ip', 'route', 'del', 'default'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))
    proc = subprocess.Popen(['ip', 'route', 'add', 'default', 'via', gw, 'dev', interface], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    syslog(LOG_INFO, decodeUTF8(proc.communicate()))
