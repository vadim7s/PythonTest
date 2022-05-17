"""Simple odbc database interface."""

import pyodbc
import datetime as dt
import numpy as np
import pandas as pd
import decimal
import string
import datetime as dt
import shutil
import os
import getpass
import adodbapi
from multiprocessing import Pool
import traceback


class Database:

    def __init__(self, name=None, server=None, dbtype=None, db=None, username=None, password=None, dsn=None):
        self.name = name
        self.db = db
        self.dbtype = dbtype
        self.dsn = dsn
        if self.dsn:
            self.connection_string = 'DSN={}'.format(self.dsn)
            if dbtype == 'Hadoop':
                self.connection = pyodbc.connect(self.connection_string, autocommit=True)
            else:
                if username is None:
                    # use Windows authentication
                    self.connection = pyodbc.connect(self.connection_string + ';TRUSTED_CONNECTION=yes')
                else:
                    self.connection = pyodbc.connect(self.connection_string + ';UID={{{}}};PWD={{{}}}'.format(username, password))
        else:
            if dbtype == 'SqlServer':
                driver_list = pyodbc.drivers()
                sql_server_drivers = ['ODBC Driver 17 for SQL Server', 'ODBC Driver 13.1 for SQL Server',
                                      'ODBC Driver 13 for SQL Server', 'ODBC Driver 11 for SQL Server',
                                      'SQL Server Native Client 11.0', 'SQL Server Native Client 10.0',
                                      'SQL Native Client', 'SQL Server']
                for driver_name in sql_server_drivers:
                    if driver_name in driver_list:
                        break
                else:
                    raise RuntimeError('Microsoft Sql Server ODBC driver is not installed. \n'
                                       'Install from https://www.microsoft.com/en-us/download/details.aspx?id=56567')
            else:
                driver_dict = {'Hana': 'HDBODBC',
                               'Hadoop': None,
                               'PI': 'PIOLEDBENT.1'}
                if not(dbtype in driver_dict.keys()):
                    raise ValueError('Database type not found.')
                driver_name = driver_dict[dbtype]
            if dbtype == 'Hana':
                if username is None:
                    self.connection_string = 'DRIVER={{{}}};SERVERNODE={{{}}};DATABASE={{{}}};TRUSTED_CONNECTION=yes'.format(driver_name, server, db, username, password)
                elif password is None:
                    self.connection_string = 'DRIVER={{{}}};SERVERNODE={{{}}};DATABASE={{{}}};UID={{{}}}'.format(driver_name, server, db, username)
                else:
                    self.connection_string = 'DRIVER={{{}}};SERVERNODE={{{}}};DATABASE={{{}}};UID={{{}}};PWD={{{}}}'.format(driver_name, server, db, username, password)
                try:
                    self.connection = pyodbc.connect(self.connection_string)
                except:
                    # If hana login fails, try to log in using the user's username and no password
                    self.connection_string = 'DRIVER={{{}}};SERVERNODE={{{}}};DATABASE={{{}}};UID={{{}}}'.format(driver_name, server, db, getpass.getuser())
                    self.connection = pyodbc.connect(self.connection_string)
            elif dbtype == 'Hadoop':
                self.connection_string = """DRIVER=Hortonworks Hive ODBC Driver;SERVICEDISCOVERYMODE=1;
                                            HOST=azmbl0002.agl.int:2181,azmbl0003.agl.int:2181,azmbl0006.agl.int:2181;
                                            ZKNamespace=hiveserver2;AUTHMECH=1;KRBREALM=AGL.INT;
                                            KRBHOSTFQDN=_HOST;KRBSERVICENAME=hive;DelegationUID={}""".format(str.lower(getpass.getuser()))
                self.connection = pyodbc.connect(self.connection_string, ansi=True, autocommit=True)
            elif dbtype == 'PI':
                self.connection_string = """Provider={};
                                            Data Source={};
                                            Integrated Security=SSPI;
                                            Persist Security Info=False;
                                            Time Zone=UTC;
                                            Command Timeout=3600;
                                            Connect Timeout=3600""".format(driver_name,server)
                self.connection = adodbapi.connect(self.connection_string)
            else:
                if username is None:
                    # use Windows authentication
                    self.connection_string = 'DRIVER={{{}}};SERVER={{{}}};DATABASE={{{}}};TRUSTED_CONNECTION=yes'.format(driver_name, server, db, username, password)
                else:
                    self.connection_string = 'DRIVER={{{}}};SERVER={{{}}};DATABASE={{{}}};UID={{{}}};PWD={{{}}}'.format(driver_name, server, db, username, password)
                self.connection = pyodbc.connect(self.connection_string)

    def run_query(self, sql):
        connection = self.connection
        cursor = connection.cursor()
        columns = []
        data_types = []
        cursor.execute(sql)

        for col in cursor.description:
            columns.append(col[0])
            data_types.append(col[1])
        data = cursor.fetchall()

        if self.dbtype == 'PI':
            # Convert data to list of tuples (instead of list of SQLrow objects)
            data = list(map(tuple, zip(*list(data.__dict__['ado_results']))))
            # Get data types
            data_types = [type(element) for element in data[0]]
            # Check which elements are a datetime
            datetime_check = [element.__name__=='datetime' for element in data_types]
            datetime_check_list = [tuple(datetime_check) for row in data]
            # Convert pywintypes.datetime to datetime.datetime
            data = [[dt.datetime(year=a.year,
                                 month=a.month,
                                 day=a.day,
                                 hour=a.hour,
                                 minute=a.minute,
                                 second=a.second) if b else a for (a,b) in zip(a,b)] for (a,b) in zip(data, datetime_check_list)]
            # Remap to list of tuples
            data = list(map(tuple, data))
            # Recompute dtypes
            data_types = [type(element) for element in data[0]]

        return data, columns, data_types

    def execute_sql(self, sql):
        if self.dbtype == 'PI':
            raise ValueError('Cannot commit to PI database.')
        connection = self.connection
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()

    def executemany_sql(self, sql, values):
        if self.dbtype == 'PI':
            raise ValueError('Cannot commit to PI database.')
        connection = self.connection
        cursor = connection.cursor()
        cursor.fast_executemany = True
        cursor.executemany(sql, values)
        connection.commit()


def connect_to_AGL_database(dbname, username=None, password=None):
    """Construct and return Database object.

    Args:
        dbname: string
        username: string or None, default None
        password: string or None, default None
    Returns:
        Database

    If username and password are None, will attempt to use Windows authentication."""

    db_params = {'LOADFCREAD': {'server': 'MDW\\MERCHANTDW', 'dbtype': 'SqlServer', 'dbname': 'LOADFC'},
                 'LOADFCWRITE': {'server': 'MDW\\MERCHANTDW', 'dbtype': 'SqlServer', 'dbname': 'LOADFC'},
                 'HANA': {'server': 'HANANode1:30015', 'dbtype': 'Hana', 'dbname': 'HP1'},
                 'WGD': {'server': 'MAPP\\MERCHANTAPP', 'dbtype': 'SqlServer', 'dbname': 'WHOLESALEGAS'},
                 'LOADFCDEV': {'server': 'GLBWI077', 'dbtype': 'SqlServer', 'dbname': 'LOADFC'},
                 'GLBWI077_MSDB': {'server': 'GLBWI077', 'dbtype': 'SqlServer', 'dbname': 'msdb'},
                 'STFORESIGHT_PROD': {'server': 'sqlfarm1pr7\sql07', 'dbtype': 'SqlServer', 'dbname': 'STFORESIGHT'},
                 'NOSTRADAMUS': {'server': 'MAPP\\MERCHANTAPP', 'dbtype': 'SqlServer', 'dbname': 'NOSTRADAMUS'},
                 'GEEK': {'server': 'GLBWI807', 'dbtype': 'SqlServer', 'dbname': 'GEEKII'},
                 'MDS': {'server': 'azmbw0553', 'dbtype': 'SqlServer', 'dbname': 'AGL_MDS'},
                 'AGL_PRICING': {'server': 'AZMAW0058.AGL.INT', 'dbtype': 'SqlServer', 'dbname': 'AGL_PRICING'},
                 'EDP': {'server': 'edpprdsqldw00.database.windows.net', 'dbtype': 'SqlServer', 'dbname': 'edpprddb'},
                 'SRDB': {'server': 'GLBWI056', 'dbtype': 'SqlServer', 'dbname': 'SAP_REPORTING'},
                 'HADOOP': {'dbtype': 'Hadoop','dsnname':'HADOOP'},
                 'Corp-PI-AF-Pri': {'server': 'Corp-PI-AF-Pri', 'dbtype': 'PI'},
                 'DATAPLAT-OW-DB2': {'server': 'azmaw0058.agl.int', 'dbtype': 'SqlServer','dbname':'pricing'},
                 'SMARTHOME': {'server': 'AZSAW0087', 'dbtype': 'SqlServer', 'dbname': 'SmartHome'},
                 'SVG_REDSHIFT': {'server': 'AZSAW0087', 'dbtype': 'SqlServer', 'dbname': 'SVG_REDSHIFT'},
                 'WIND_ORACLE': {'dbtype': 'SqlServer'},
                 'INFOPROD': {'server': 'sqlfarm1pr7\sql07', 'dbtype': 'SqlServer', 'dbname': 'INFOPROD'},
                 'NEW_ENERGY': {'server': 'ne-dataplatform-server-prod.database.windows.net', 'dbtype': 'SqlServer', 'dbname': 'ne-dataplatform-db'},
                 'VIVID': {'server': 'glbwi868', 'dbtype': 'SqlServer', 'dbname': 'VIVID'},
                 'CLV_TACTICAL': {'server': 'azmaw0058.agl.int', 'dbtype': 'SqlServer', 'dbname': 'pricing'}}
    db_properties = db_params[dbname]
    for key in ['server', 'dbtype', 'dbname', 'username', 'password', 'dsnname']:
        if key not in db_properties:
            db_properties[key] = None
    if dbname == 'WIND_ORACLE':
        if os.name == 'nt':
            db_properties['server'] = 'AZMBW0074'
            db_properties['dbname'] = 'master'
        else:
            db_properties['server'] = 'wholesale-nprd-sqlsvr-primary.database.windows.net'
            filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'db_config.txt')
            with open(filename) as f:
                db_properties['username'] = f.readline().replace('\n', '')
                db_properties['password'] = f.readline().replace('\n', '')
    if username is not None:
        db_properties['username'] = username
    if password is not None:
        db_properties['password'] = password
    return Database(dbname, server=db_properties['server'], dbtype=db_properties['dbtype'], db=db_properties['dbname'],
                    username=db_properties['username'], password=db_properties['password'], dsn=db_properties['dsnname'])


def sql_from_file(filename, find_replace=None, dbtype='SqlServer'):
    """
    Load filename and replaces strings according to find_replace dictionary.

    Args:
        filename: string giving filepath of query
        find_replace: dictionary of strings to replace in query
        dbtype: string, either 'Hana' or 'SqlServer'. This is used to format dates.

    Returns:
        string
    """

    with open(filename) as f:
        sql = f.read()
    date_formatter = get_date_formatter(dbtype)
    if find_replace:
        for i_key in find_replace:
            if issubclass(type(find_replace[i_key]), dt.date) or issubclass(type(find_replace[i_key]), dt.datetime):
                if not dbtype:
                    raise ValueError('You must specify the database type when find_replace contains dates.')
                sql = sql.replace(i_key, date_formatter(find_replace[i_key]))
            else:
                sql = sql.replace(i_key, str(find_replace[i_key]))
    return sql


def get_date_formatter(dbtype, include_quotes=True):
    """ Return date formatting function for particular database type."""
    if dbtype == 'Hana':
        if include_quotes:
            return lambda d: "'" + d.strftime('%Y-%m-%d %H:%M:%S') + "'"
        else:
            return lambda d: d.strftime('%Y-%m-%d %H:%M:%S')
    elif dbtype == 'SqlServer':
        if include_quotes:
            return lambda d: "'" + d.strftime('%d-%b-%Y %H:%M:%S') + "'"
        else:
            return lambda d: d.strftime('%Y-%m-%d %H:%M:%S')
    else:
        raise ValueError('Database type {} not recognised.'.format(dbtype))


def df_from_sql(db, sql, frequency=None):
    """Connect to database, execute sql query and return results in dataframe.

    Args:
        db: string or Database object
        sql: string
        frequency: string ('D' for daily, 'H' for hourly, 'HH' for half-hourly) or None. If not None, make the first
        column returned by query into a time index, otherwise just use default index

    Returns:
        pd.DataFrame"""

    # runs query and puts results in dataframe
    # if frequency is specified, makes a time index, otherwise default index
    #print(sql) # remode this line in prod
    if type(db) == str:
        db = connect_to_AGL_database(db)
    else:
        db = db
    (rows, cols, data_types) = db.run_query(sql)
    if len(rows) == 0:
        return pd.DataFrame(columns=cols)
    else:
        if frequency in ('D', 'H', 'HH'):
            df = pd.DataFrame([r[1:] for r in rows], index=[pd.Timestamp(r[0]) for r in rows], columns=cols[1:])
            df.groupby(level=0).last() #eliminate duplicate values in index if necessary (e.g. extra row for daylight savings time)
        elif frequency == 'P':
            index = pd.MultiIndex.from_tuples(list((pd.Timestamp(r[0]), r[1]) for r in rows), names=['date', 'period'])
            df = pd.DataFrame([r[2:] for r in rows], index=index, columns=cols[2:])
            df.groupby(level=[0, 1]).last()
        else:
            df = pd.DataFrame.from_records(rows, columns=cols)
        # convert decimal columns to float
        for col in df.columns:
            if type(df[col].iloc[0]) in [decimal.Decimal]:
                df[col] = df[col].astype(np.float64)
            if type(df[col].iloc[0]) in [np.datetime64, dt.datetime, dt.date]:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        return df


def df_from_sql_wrapper(db, sql, frequency=None):
    """Wrap df_from_sql in try-catch, so that if one query fails in df_from_sql_parallel, we can still return the
    others."""

    try:
        return df_from_sql(db, sql, frequency)
    except:
        traceback.print_exc()


def df_from_sql_parallel(arg_list, pool_size=None):
    """Run several database queries in parallel. If using this function, you MUST wrap in the condition
    if __name__ == '__main__'. See the readme for example usage.

    Args:
        arg_list: a list of tuples of arguments to pass to df_from_sql.
            Should have the format ((db1, sql1, freq1), (db2, dql2, freq2), ...)
        pool_size: number of queries to run in parallel. If None, defaults to number of cores on your machine. You
            may need to reduce this if you are running several queries on the same database and causing it to crash.

    Returns:
        tuple of pd.DataFrame"""

    if pool_size is None:
        p = Pool()
    else:
        p = Pool(pool_size)
    result = p.starmap_async(df_from_sql_wrapper, arg_list)
    p.close()
    p.join()
    result.wait()
    return result.get()


def write_data(data_to_write, database, schema, table):
    """Write dataframe to database.

    Args:
        data_to_write: pd.DataFrame
        database: Database object
        schema: string
        table: string"""

    if len(data_to_write) == 0:
        return

    data_types_df = [data_to_write[col].dtype.type for col in data_to_write.columns]
    if database.dbtype == 'SqlServer':
        # get data types from database
        sql = "select data_type from [{}].information_schema.columns where table_schema = '{}' and table_name = '{}' order by ordinal_position".format(database.db, schema, table)
        data_types_qry_result = database.run_query(sql)[0]
        data_types_db = [row[0] for row in data_types_qry_result]

        if data_to_write.shape[1] != len(data_types_db):
            raise ValueError('Dataframe has {} columns, but database table has {} columns'.format(data_to_write.shape[1], len(data_types_db)))

        # check datatypes: if db type is numeric, df type must be as well, and similarly for datetime, string
        for i in range(len(data_types_db)):
            if data_types_db[i] in ['float', 'real', 'bigint','int','smallint','tinyint']:
                if not(issubclass(data_types_df[i], np.number)):
                    raise ValueError('Dataframe column {} has type {} but database column {} has type {}'.format(i, data_types_df[i], i+1, data_types_db[i]))
            elif data_types_db[i] in ['datetime', 'datetime2', 'smalldatetime', 'date', 'time']:
                if not(issubclass(data_types_df[i], dt.datetime)) and not(issubclass(data_types_df[i], np.datetime64)):
                    raise ValueError('Dataframe column {} has type {} but database column {} has type {}'.format(i, data_types_df[i], i+1, data_types_db[i]))
            elif data_types_db[i] in ['char', 'varchar', 'text']:
                if not(issubclass(data_types_df[i], np.object_)):
                    raise ValueError('Dataframe column {} has type {} but database column {} has type {}'.format(i, data_types_df[i], i+1, data_types_db[i]))
    else:
        # just assume the datatypes are correct
        data_types_db = [None]*len(data_types_df)
        for i in range(len(data_types_db)):
            if issubclass(data_types_df[i], np.number):
                data_types_db[i] ='float'
            elif (issubclass(data_types_df[i], dt.datetime)) or (issubclass(data_types_df[i], np.datetime64)):
                data_types_db[i] = 'datetime'
            elif issubclass(data_types_df[i], np.object_):
                data_types_db[i] = 'char'

    # replace nulls with None
    formatted_data = data_to_write.where(data_to_write.notnull(), None)

    # insert
    values = [list(formatted_data.values[i]) for i in range(formatted_data.shape[0])]
    sql = "insert into {}.{} values ({})".format(schema, table, ', '.join(['?']*formatted_data.shape[1]))
    database.executemany_sql(sql, values)


def bulk_insert_from_file(db, filename, local_folder, dbserver_folder, schema, table):
    """Bulk insert from csv. Copy csv from local folder to database server, insert, then delete server copy of folder.

    Args:
        db: Database object
        filename: name of csv file to load
        local_folder: path to folder containing csv file on local machine
        db_server_folder: path folder csv file should be copied to, on db server
        schema: schema to write to
        table: table to write to
    """
    if db.dbtype == 'PI':
        raise ValueError('Cannot commit to PI database.')
    shutil.copy(os.path.join(local_folder, filename), os.path.join(dbserver_folder, filename))
    sql = "bulk insert {}.{} from '{}' with (fieldterminator=',', rowterminator = '0x0a', rows_per_batch=10000, " \
          "tablock)".format(schema, table, os.path.join(dbserver_folder, filename))
    connection = pyodbc.connect(db.connection_string)
    cursor = connection.cursor()
    cursor.execute(sql)
    connection.commit()
    os.remove(os.path.join(dbserver_folder, filename))

    
def update_db_from_sql(database_name, sql, table_name):
    """Connect to database, execute sql query and update database table

    Args:
        database_name: string or Database object
        sql: string
    Returns:
        r1 : integer number of rows in target table before the query is run
        r2 : integer number of rows in target table after the query has updated the table
    """

    if type(database_name) == str:
        db = connect_to_AGL_database(database_name)
    else:
        db = database_name

    # check num rows before update
    try:
        (rows, columns, datatypes) = db.run_query('select count(*) from {}'.format(table_name))
        r1 = rows[0][0]
    except:
        # table does not exist
        r1 = 0

    # runs query and updates database
    db.execute_sql(sql)

    # check num rows after update
    try:
        (rows, columns, datatypes) = db.run_query('select count(*) from {}'.format(table_name))
        r2 = rows[0][0]
    except:
        # table does not exist
        r2 = 0

    return [r1, r2]
