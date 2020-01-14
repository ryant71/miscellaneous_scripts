#!/usr/bin/env python

try:
    import progress_bar
    use_mdp = True
except ImportError:
    use_mdp = False

import sys
import time
import math
import sqlalchemy as sa

from sdslib import poltranscols, comtranscols, headcols, tailcols
from sdslib import line2sqldict, write2table
from sdslib import FileInfo

# TODO make this part of the FileInfo object (parse_params method)
skip_fileinfo = 0
skip_sanity = 0

def dofile(filepath):
    polc = 0
    comc = 0
    inserts = 0
    #infile = file(filepath).read()
    fi = FileInfo(filepath)
    print fi.FileName
    if not fi.sanity_check() and not skip_sanity:
        print 'Sanity Check Failed!', fi.SanityFail, fi.CycleNumber
        print 'Skipping this file'
        return
        #sys.exit(1)
    if not skip_fileinfo:
        try:
            file_id = fi.addfileinfo()
        except sa.exceptions.IntegrityError:
            print 'Already processed this file'
            return
    else:
        file_id = 0
    infile = fi.in_lines
    if use_mdp:
        iter = progress_bar.progressinfo(infile)
    else:
        iter = infile
    start = time.time()
    ROWCHUNKS = 10000
    rc = 0
    comsql = []
    polsql = []
    polrowsleft = fi.NumPolRecs
    comrowsleft = fi.NumComRecs
    for line in iter:
        rc += 1
        line = line.strip()
        if line[0:2] == '10':
            polc += 1
            polrowsleft -= 1
            dict = poltranscols
            polsql.append(line2sqldict(line, dict, file_id))
            if math.fmod(len(polsql),ROWCHUNKS)==0 or polrowsleft <= ROWCHUNKS:
                inserts += write2table(polsql, dict)
                polsql = []
        elif line[0:2] == '20':
            comc += 1
            comrowsleft -= 1
            dict = comtranscols
            comsql.append(line2sqldict(line, dict, file_id))
            if math.fmod(len(comsql),ROWCHUNKS)==0 or comrowsleft <= ROWCHUNKS:
                inserts += write2table(comsql, dict)
                comsql = []
        elif line[0:2] == '00':
            dict = headcols
        elif line[0:2] == '99':
            dict = tailcols
        else:
            print 'Unidentified line!'
            sys.exit(1)
    del iter, infile
    ttime = time.time() - start
    print '%s: comrecs: %d, polrec: %d, total: %d, inserts: %d (time=%d)' \
                % (fi.FileName, comc, polc, comc+polc, inserts, ttime)
    if not fi.final_check(polc, comc):
        print 'Failed Final Check!', fi.SanityFail
        sys.exit(1)
    fi.set_checksum()

def main():
    try:
        infiles = sys.argv[1:]
    except:
        print 'Usage: %s <file1> ... <fileN>' % (sys.argv[0],)
        sys.exit(1)
    for filepath in infiles:
        dofile(filepath)


if __name__=="__main__":

    main()
