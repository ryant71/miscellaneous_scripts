#!/usr/bin/env python

"""
Keep this in mind: http://cliff.readthedocs.org/en/latest/demoapp.html

"""

import csv
import sys
import sqlalchemy as sa
import warnings
from optparse import OptionParser

def handle_opts():
    usage = 'Usage: %prog [options] mysql://un:pw@host/schema/table <csvfile>'
    parser = OptionParser(usage=usage)
    parser.add_option("-i", "--insert", action="store_true", dest="do_insert",
                      help="Insert the CSV file into the table")
    parser.add_option("-u", "--update", action="store", dest="update_on_col",
                      default=False,
                      help="Input Data will UPDATE the target table")
    parser.add_option("-d", "--delete", action="store", dest="do_delete",
                      help="Delete rows in in CSV from database")
    return parser.parse_args(), parser

"""
Keep this in mind for later use.
Thanks Amir!
def probably_equal(str1, str2, threshhold=0.8):
    import difflib
    s = difflib.SequenceMatcher(None, str1, str2)
    ratio = s.ratio()
    if ratio >= threshhold:
        return True, ratio
    return False, ratio
"""

def stdout(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()

# open a csv file of given type
#
def parse_csv(file):
    csv.register_dialect('csv', delimiter=',', quoting=csv.QUOTE_ALL)
    return csv.reader(open(file, "rb"))


"""
Store Python warnings in a list for later use.
"""
def mywarning(message, category, filename, lineno, file=None, line=None):
    errors.append(warnings.formatwarning(message, category, filename='',
                                         lineno=''))

warnings.showwarning = mywarning
warnings.simplefilter('always')

"""
Get a response without user hitting enter.
"""
def getch():
    import os, tty
    fd = sys.stdin.fileno()
    tty_mode = tty.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        ch = os.read(fd, 1)
    finally:
        tty.tcsetattr(fd, tty.TCSAFLUSH, tty_mode)
    return ch

def columns_compare(tableobj, firstrow):
    tblcols = tableobj.columns.keys()
    maxlength = 0
    td = []
    inc = 1
    td.append(('Table', 'CSV', ''))
    for col in tblcols:
        if len(col)>maxlength:
            maxlength = len(col)
        if col in firstrow:
            td.append((col, '[yes]', ''))
        else:
            td.append((col, '[no]', ' <--'))
            inc += 1
    for col in firstrow:
        if col not in tblcols:
            td.insert(firstrow.index(col)+inc, ('[no]', col, ' <--'))
    td.insert(1, ('-'*(maxlength+1), '-'*(maxlength+1), ''))
    s = '\t|%%%ds|%%%ds|%%s' % (maxlength+1, maxlength+1)
    for line in td:
        print(s % line)


if __name__=="__main__":
    """
    I have way too much stuff below
    """

    (options, args), parser = handle_opts()
    update_on_col = options.update_on_col
    do_insert = options.do_insert
    do_delete = options.do_delete

    if options.update_on_col:
        method = 'UPDATE'
    elif options.do_insert:
        method = 'INSERT'
    elif options.do_delete:
        method = 'DELETE'
    if options.update_on_col and options.do_insert:
        parser.error("options -i and -u are mutually exclusive")

    try:
        dbcred = args[0]
        csvfile = args[1]
        table = dbcred.split('/')[-1]
        dbcred = dbcred.replace('/%s' % table, '')
    except:
        parser.print_help()
        sys.exit()

    try:
        #updates = open(csvfile, 'r').readlines()
        updates = parse_csv(csvfile)
    except IOError:
        parser.error('Cannot open %s' % (csvfile,))

    db = sa.create_engine(dbcred)
    meta = sa.MetaData()
    meta.bind = db
    thetable = sa.Table(table, meta, autoload=True)

    print('DB: %s' % dbcred)
    print('Table: %s' % table)
    print('File: %s' % csvfile)
    print('Method: %s' % method)
    if update_on_col:
        print('  Update on Column: %s' % update_on_col)
    print()

    # get colnames
    coldict = {}
    #firstrow = [item.strip() for item in updates[0].split(',')]
    #therest = updates[1:]
    firstrow = updates.next()
    numcols = len(firstrow)
    for i in range(numcols):
        coldict[i] = firstrow[i]

    print('Table/File comparison:\n')
    columns_compare(thetable, firstrow)
    stdout('\nProceed?: y/n '),
    resp = getch()
    if resp not in ['y','Y','yes']:
        print('\nNo. Okay, exiting...')
        sys.exit(0)

    errors = []
    stdout('\nRows: ')
    for row in updates:
        #row = row.strip()
        #if row=='':
        #    continue
        #row = row.split(',')
        sqldict = {}
        for i in range(numcols):
            sqldict[coldict[i]] = row[i]
        if update_on_col:
            thecol=thetable.columns[update_on_col]
            update_on_col_val = sqldict[update_on_col]
            del sqldict[update_on_col]
            thetable.update(thecol==update_on_col_val,
                            values=sqldict).execute()
        elif do_insert:
            thetable.insert(sqldict).execute()
        elif do_delete:
            where = 'where '
            for item in sqldict:
                try:
                    sqldict[item] = int(sqldict[item])
                except:
                    pass
                if type(sqldict[item])==type(1):
                    where += ' %s = %s and' % (item, sqldict[item])
                else:
                    where += ' %s = "%s" and' % (item, sqldict[item])
            where = where[:-3]
            sql = "delete from %s %s" % (thetable.name, where)
            db.execute(sql)
        stdout('.')

    stdout('\nErrors:\n')
    for e in errors:
        stdout(e)


