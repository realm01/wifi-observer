# Created by: Anastassios Martakos
# Copyright (c) 2016 Anastassios Martakos

#!/usr/bin/env python3.4

import sqlite3, csv
from syslog import syslog, LOG_INFO, LOG_ERR

def connectDB(db):
    return sqlite3.connect(db, 20)

def writeCheck(**kwargs):
    bssid_id = kwargs.get('sanity')['bssid']

    if bssid_id != 'NULL':
        if(not checkEntry(kwargs.get('db_conn'), 'bssids', 'bssid', kwargs.get('sanity')['bssid'])):
            insertSingle(kwargs.get('db_conn'), 'bssids', 'bssid', kwargs.get('sanity')['bssid'])
        bssid_id = checkEntry(kwargs.get('db_conn'), 'bssids', 'bssid', kwargs.get('sanity')['bssid'])

    if(not checkEntry(kwargs.get('db_conn'), 'ssids', 'ssid', kwargs.get('sanity')['ssid'])):
        insertSingle(kwargs.get('db_conn'), 'ssids', 'ssid', kwargs.get('sanity')['ssid'])
    ssid_id = checkEntry(kwargs.get('db_conn'), 'ssids', 'ssid', kwargs.get('sanity')['ssid'])

    time_needed_conn = 'NULL' if kwargs.get('sanity')['time_needed_conn'] > kwargs.get('timeouts')['conn'] else kwargs.get('sanity')['time_needed_conn']
    time_needed_dhcp = 'NULL' if kwargs.get('sanity')['time_needed_dhcp'] > kwargs.get('timeouts')['dhcp'] or time_needed_conn == 'NULL' else kwargs.get('sanity')['time_needed_dhcp']
    ping_average = 'NULL' if kwargs.get('sanity')['ping_average'] == 0 else str(kwargs.get('sanity')['ping_average'])

    if time_needed_conn != 'NULL':
        time_needed_conn = str("{0:.5f}".format(float(time_needed_conn)))
    if time_needed_dhcp != 'NULL':
        time_needed_dhcp = str("{0:.5f}".format(float(time_needed_dhcp)))

    for code in kwargs.get('sanity')['errors']:
        sql_string = 'SELECT id FROM errors WHERE code="' + code['code'] + '"'
        try: entries = executeSQL(kwargs.get('db_conn'), sql_string)
        except: return 'get error'

        fentries = entries.fetchall()
        if len(fentries) == 0:
            sql_string = 'INSERT INTO  errors(code) VALUES("' + code['code'] + '")'
            info = {}
            try: entries = executeSQL(kwargs.get('db_conn'), sql_string, info)
            except: return 'insert error'

            code['id'] = info['id']
            commit(kwargs.get('db_conn'))
        else:
            code['id'] = fentries[0][0]

    location_id = '0'
    sql_string = 'SELECT id FROM locations WHERE location="' + kwargs.get('location') + '"'
    try: entries = executeSQL(kwargs.get('db_conn'), sql_string)
    except: return 'get location'

    lentries = entries.fetchall()
    if len(lentries) == 0:
        sql_string = 'INSERT INTO locations(location) VALUES("' + kwargs.get('location') + '")'
        linfo = {}
        try: executeSQL(kwargs.get('db_conn'), sql_string, linfo)
        except: return 'insert location'
        commit(kwargs.get('db_conn'))
        location_id = linfo['id']
    else:
        location_id = lentries[0][0]

    sql_string = 'INSERT INTO data(time_needed_conn, time_needed_dhcp, ping_average, time_start, dbm, ssid_fk, bssid_fk, location_fk) VALUES(' + str(time_needed_conn) + ', ' + str(time_needed_dhcp) + ', ' + str(ping_average) + ', ' + str(int(kwargs.get('sanity')['time_start'])) + ', ' + str(kwargs.get('sanity')['dbm']) + ', ' + str(ssid_id) + ', ' + str(bssid_id) + ',' + str(location_id) + ')'

    info = {}
    try: entries = executeSQL(kwargs.get('db_conn'), sql_string, info)
    except: return 'insert main'

    commit(kwargs.get('db_conn'))


    for code in kwargs.get('sanity')['errors']:
        sql_string = 'INSERT INTO errors_data(data_fk, error_fk) VALUES(' + str(info['id']) + ', ' + str(code['id']) + ')'
        try: executeSQL(kwargs.get('db_conn'), sql_string)
        except: return 'insert errrors_data'
        commit(kwargs.get('db_conn'))

    return info['id']

def checkEntry(db_conn, table, column, search):
    sql_string = 'SELECT id FROM ' + table + ' WHERE ' + column + '="' + search + '"'
    try: entries = executeSQL(db_conn, sql_string)
    except: return True

    for entry in entries.fetchall():
        return entry[0]

    commit(db_conn)

    return False

def insertSingle(db_conn, table, column, value):
    sql_string = 'INSERT INTO ' + table + '(' + column + ')' + ' VALUES("' + str(value) + '")'
    try: entries = executeSQL(db_conn, sql_string)
    except: return True
    commit(db_conn)

    return False

def getAllDates(db_path):
    db_conn = connectDB(db_path)

    sql_string = 'SELECT DISTINCT date(time_start, "unixepoch", "localtime", "start of day") FROM data'
    try: entries = executeSQL(db_conn, sql_string)
    except: return True
    final = entries.fetchall()
    db_conn.close()
    return final

def getSSIDs(db_path):
    db_conn = connectDB(db_path)

    final = []

    sql_string = 'SELECT id, ssid FROM ssids'
    try: entries = executeSQL(db_conn, sql_string)
    except: return True
    for entry in entries.fetchall():
        final.append({ 'name' : entry[1], 'where' : 'AND ssid_fk=' + str(entry[0]) })
    db_conn.close()

    return final

def getSSIDsName(db_path):
    db_conn = connectDB(db_path)
    final = []

    sql_string = 'SELECT ssid FROM ssids'
    try: entries = executeSQL(db_conn, sql_string)
    except: return True
    for entry in entries:
        final.append(entry[0])
    db_conn.close()

    return final

def generateCSV(db_conn, csv_file, start, end):
    sql_string = 'select data.id, datetime(time_start, "unixepoch") as time_start_coll, time_needed_conn IS NOT NULL as time_needed_conn_null, time_needed_dhcp IS NOT NULL as time_needed_dhcp_null, ssids.ssid, bssids.bssid, locations.location from data left join ssids on data.ssid_fk=ssids.id left join bssids on data.bssid_fk=bssids.id left join locations on data.location_fk=locations.id where cast(strftime("%W", time_start_coll) as integer) >= ' + start + ' and cast(strftime("%W", time_start_coll) as integer) <= ' + end + ' order by datetime(time_start, "unixepoch") asc'

    try: entries = executeSQL(db_conn, sql_string)
    except: return True

    ID = 0
    TIMESTAMP = 1
    CONN_NULL = 2
    DHCP_NULL = 3
    SSID = 4
    BSSID = 5
    LOCATION = 6

    with open(csv_file, 'w') as cf:
        fieldnames = [ 'id', 'timestamp', 'conn', 'dhcp', 'ssid', 'bssid', 'location' ]
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for entry in entries.fetchall():
            writer.writerow({'id' : entry[ID], 'timestamp' : entry[TIMESTAMP], 'conn' : entry[CONN_NULL], 'dhcp' : entry[DHCP_NULL], 'ssid' : entry[SSID], 'bssid' : entry[BSSID], 'location' : entry[LOCATION]})

def getStats(db_path):
    db_conn = connectDB(db_path)

    DATE = 0
    SSID = 1
    SSID_NAME = 2
    BSSID = 3
    BSSID_NAME = 4
    ID_COUNT = 5
    DHCP_NULL = 6
    CONN_NULL = 7

    # stats data structure
    # [ { <date> :    { <type> : { <name> {
    #                                       <total_checks> : <int>
    #                                       <conn_null_count> : <int>
    #                                       <dhcp_null_count : <int>
    #                                   }
    #                           }
    #               }
    # ] }
    #
    # type can be:  total
    #               ssid
    #               bssid

    stats = []

    # glob stat data structure is the same as stats
    # just without the <date> and the array arround it

    glob_stats = {}

    # date_mapper data structure
    # {
    #   <date> : <(int)array-index>
    # }

    date_mapper = {}

    types = [ 'ssid', 'bssid' ]

    sql_string = 'select date(time_start, "unixepoch", "localtime", "start of day") as time_start_coll, ssid_fk, ssids.ssid, bssid_fk, bssids.bssid, count(data.id),time_needed_dhcp IS NULL as time_needed_dhcp_null,time_needed_conn IS NULL as time_needed_conn_null from data left join ssids on data.ssid_fk=ssids.id left join bssids on data.bssid_fk=bssids.id group by ssid_fk,bssid_fk, time_needed_dhcp IS NULL, time_needed_conn IS NULL, date(time_start, "unixepoch", "localtime", "start of day") order by datetime(time_start, "unixepoch", "localtime", "start of day") desc'
    try: entries = executeSQL(db_conn, sql_string)
    except: return True
    for entry in entries.fetchall():
        for type in types:
            try: date_mapper[entry[DATE]]
            except:
                stats.append({})
                date_mapper[entry[DATE]] = len(stats) - 1


            try: stats[date_mapper[entry[DATE]]][entry[DATE]]
            except: stats[date_mapper[entry[DATE]]][entry[DATE]] = {}

            try: stats[date_mapper[entry[DATE]]][entry[DATE]][type]
            except: stats[date_mapper[entry[DATE]]][entry[DATE]][type] = {}

            if(type == 'ssid'):
                name = entry[SSID_NAME]
            elif(type == 'bssid' and entry[BSSID] != None):
                name = entry[BSSID_NAME]
            elif(type == 'bssid' and entry[BSSID] == None):
                name = "no connection"

            try: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]
            except: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name] = {}
            try: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['total_checks']
            except: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['total_checks'] = 0
            stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['total_checks'] += entry[ID_COUNT]
            try: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['conn_null_count']
            except: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['conn_null_count'] = 0
            try: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['dhcp_null_count']
            except: stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['dhcp_null_count'] = 0
            stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['conn_null_count'] += entry[ID_COUNT] if entry[CONN_NULL] == 1 else 0
            stats[date_mapper[entry[DATE]]][entry[DATE]][type][name]['dhcp_null_count'] += entry[ID_COUNT] if entry[DHCP_NULL] == 1 and entry[CONN_NULL] == 0 else 0

            try: glob_stats[type]
            except: glob_stats[type] = {}
            try: glob_stats[type][name]
            except: glob_stats[type][name] = {}
            try: glob_stats[type][name]['total_checks']
            except: glob_stats[type][name]['total_checks'] = 0
            glob_stats[type][name]['total_checks'] += entry[ID_COUNT]
            try: glob_stats[type][name]['conn_null_count']
            except: glob_stats[type][name]['conn_null_count'] = 0
            try: glob_stats[type][name]['dhcp_null_count']
            except: glob_stats[type][name]['dhcp_null_count'] = 0
            glob_stats[type][name]['conn_null_count'] += entry[ID_COUNT] if entry[CONN_NULL] == 1 else 0
            glob_stats[type][name]['dhcp_null_count'] += entry[ID_COUNT] if entry[DHCP_NULL] == 1 and entry[CONN_NULL] == 0 else 0

        try: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']
        except: stats[date_mapper[entry[DATE]]][entry[DATE]]['total'] = {}
        try: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']
        except: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total'] = {}
        try: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['total_checks']
        except: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['total_checks'] = 0
        stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['total_checks'] += entry[ID_COUNT]
        try: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['conn_null_count']
        except: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['conn_null_count'] = 0
        try: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['dhcp_null_count']
        except: stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['dhcp_null_count'] = 0
        stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['conn_null_count'] += entry[ID_COUNT] if entry[CONN_NULL] == 1 else 0
        stats[date_mapper[entry[DATE]]][entry[DATE]]['total']['total']['dhcp_null_count'] += entry[ID_COUNT] if entry[DHCP_NULL] == 1 and entry[CONN_NULL] == 0 else 0


        try: glob_stats['total']
        except: glob_stats['total'] = {}
        try: glob_stats['total']['total']
        except: glob_stats['total']['total'] = {}
        try: glob_stats['total']['total']['total_checks']
        except: glob_stats['total']['total']['total_checks'] = 0
        glob_stats['total']['total']['total_checks'] += entry[ID_COUNT]
        try: glob_stats['total']['total']['conn_null_count']
        except: glob_stats['total']['total']['conn_null_count'] = 0
        try: glob_stats['total']['total']['dhcp_null_count']
        except: glob_stats['total']['total']['dhcp_null_count'] = 0
        glob_stats['total']['total']['conn_null_count'] += entry[ID_COUNT] if entry[CONN_NULL] == 1 else 0
        glob_stats['total']['total']['dhcp_null_count'] += entry[ID_COUNT] if entry[DHCP_NULL] == 1 and entry[CONN_NULL] == 0 else 0

        db_conn.close()
    return [stats, glob_stats]

def commit(db_conn):
    try:
        db_conn.commit()
    except sqlite3.Error as e:
        print('sql error: ' + e.args[0])
        syslog(LOG_ERR, 'sql error: ' + e.args[0])
        raise e

def executeSQL(db_conn, sql_string, add_information={}):
    c = db_conn.cursor()

    try:
        entries = c.execute(sql_string)
        add_information['id'] = c.lastrowid
    except sqlite3.Error as e:
        print('sql error: ' + e.args[0])
        syslog(LOG_ERR, 'sql error: ' + e.args[0])
        raise e

    return entries
