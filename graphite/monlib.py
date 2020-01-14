#
# library for monitoring scripts
#
import time
import syslog
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, select


def time_dbcall(dbcall, msg=''):
    start = time.time()
    ret = dbcall.fetchall()
    ts = time.time()
    syslog.syslog(syslog.LOG_INFO, msg+': %f sec' % (ts - start))
    return ret

def loginfo(msg):
    syslog.syslog(syslog.LOG_INFO, msg)

def logerr(msg):
    syslog.syslog(syslog.LOG_ERR, msg)


def mkpersist():
    persistdb_engine = sa.create_engine('sqlite:////opt/monitoring/graphite_persist.db')
    persistdb_conn = persistdb_engine.connect()
    persist_table = sa.Table('persist', metadata,
        Column('scriptname', String(100), primary_key = True),
        Column('index_table', String(100), nullable = False),
        Column('index_column', String(100), nullable = False),
        Column('index_value', Integer, nullable = False))

    # create sqlite table if not exists
    persist_table.create(persistdb_engine, checkfirst=True)
    return persistdb_conn, persist_table


def get_index_value(scriptname):
    s = select([persist_table]).where(persist_table.c.scriptname == scriptname)
    ret = persistdb_conn.execute(s).fetchone()
    if not ret:
        index_value = 0
        ins = persist_table.insert().values(scriptname = scriptname,
                                            index_table = index_table,
                                            index_column = index_column,
                                            index_value = index_value)
        ret = persistdb_conn.execute(ins)
    else:
        index_value = int(ret['index_value'])
    return index_value



