#
# sdslib.py
#

import os
import sys
import time
import datetime
import sha
from UserDict import UserDict
from decimal import Decimal
import sqlalchemy as sa

db = sa.create_engine('mysql://root:r00t@localhost/omfeed')
metadata = sa.MetaData()
metadata.bind = db

file_tbl              = sa.Table('file',              metadata, autoload=True)
commission_infile_tbl = sa.Table('commission_infile', metadata, autoload=True)
policy_infile_tbl     = sa.Table('policy_infile',     metadata, autoload=True)

"""
1. Move count file lines per type into step 1 (early in process)
2. create a stop step at the end of step 1 (file processing) - use the checksum
   field to have a stop, process, or processed already flag?
3. pull out file line counts from step 2 (keep table counts?), but do the full
   footer compare still and ensure correct.
4. After processing info into files check that the three join fields are 
   unique. (select fields, count(*), group by fields having count(*)>1) - 
   should never be non unique.
"""

class FileInfo(UserDict):
    """
    class for file information
    instantiation: FileInfo('/path/to/file.ext')
    """
    def __init__(self, filepath=None):
        """kinda like a constructor but not quite"""
        UserDict.__init__(self)
        infile_obj = open(filepath, 'r')
        infile = infile_obj.read()
        infile_obj.seek(0)
        self.in_lines = infile_obj.readlines()
        self.firstline = self.in_lines[0].strip()
        self.lastline = self.in_lines[-1].strip()
        # attributes
        self.SanityFail = ''
        self.NumPolRecs = int(self.lastline[tailcols[1][1]:tailcols[1][2]])
        self.NumComRecs = int(self.lastline[tailcols[2][1]:tailcols[2][2]])
        self.CycleNumber = int(self.firstline[headcols[2][1]:headcols[2][2]])
        self.HeaderDate = self.firstline[headcols[3][1]:headcols[3][2]]
        self.FileName = os.path.basename(filepath)
        self.FileNameDate = self.FileName.split('_')[2].split('.')[0][:8]
        self.polrec_cnt = len([l for l in self.in_lines if l.startswith('10')])
        self.comrec_cnt = len([l for l in self.in_lines if l.startswith('20')])
        # data
        stats = os.stat(filepath)
        self['FileName'] = self.FileName
        self['FileSizeBytes'] = stats[6]
        self['ProcessedDate'] = datetime.datetime.now()
        self['FileHash'] = sha.new(infile).hexdigest()
        self['NumberOfRows'] = len(infile.split('\n'))
        self['NumPolRecs'] = self.NumPolRecs
        self['NumComRecs'] = self.NumComRecs
        self['HeaderDate'] = self.HeaderDate
        self['CycleNumber'] = self.CycleNumber
        self['CheckSum'] = 0

    # methods

    def handle_parameters(self):
        """parse commandline parameters"""
        pass

    def addfileinfo(self):
        """adds FileInfo instance to db via sqlalchemy"""
        self.file_id = file_tbl.insert(self.data
                                      ).execute().last_inserted_ids()[0]
        return self.file_id

    def set_checksum(self):
        """ """
        return file_tbl.update(file_tbl.c.FileID==self.file_id,
                               values={'CheckSum': 1}).execute()

    def sanity_check(self):
        """ """
        self.max_cycle_number = max([l[0] for l in sa.select(
                                                  [file_tbl.c.CycleNumber]
                                              ).execute().fetchall()])
        if self.CycleNumber <= self.max_cycle_number:
            self.SanityFail = 'CycleNumber is not greater than max (%s)' % self.max_cycle_number
            return False
        if not (self.FileNameDate==self.HeaderDate):
            self.SanityFail = 'File date != Header date'
            return False
        if not (self.polrec_cnt==self.NumPolRecs):
            self.SanityFail = 'Policy line count != Footer Policy Records'
            return False
        if not (self.comrec_cnt==self.NumComRecs):
            self.SanityFail = 'Commission line count != Footer Comm. Records'
            return False
        return True

    def final_check(self, polcount, comcount):
        """ """
        if not (polcount==self.NumPolRecs):
            self.SanityFail = 'Policy Inserts != Footer Policy Records'
            return False
        if not (comcount==self.NumComRecs):
            self.SanityFail = 'Commission Inserts != Footer Comm. Records'
            return False
        return True


class OMFeed():
    """
    omfeed database class
    """
    def __init__(self, fileinfo=None):
        """
        Instantiate some variables here. Get some values from the FileInfo()
        object.
        """
        pass

    def pre_check(self):
        """
        Check that tables in omfeed database are in a ready state for
        the current processing task.
        """
        pass

    def prepare(self):
        pass

    def run(self):
        pass

    def post_check(self):
        pass

    def zeroize(self):
        pass


def line2sqldict(line, dict, file_id):
    """	
	Take a line and dictionary and, based on the rules in
	the dictionary break the line into parts and assemble as
	a dictionary (sqldict) to return to sqlalchemy to process
	"""
    sqldict = {}
    sqldict['file_id'] = file_id
    keys = sorted(dict.keys())
    for key in keys:
        desc     = dict[key][0]
        startpos = dict[key][1]
        endpos   = dict[key][2]
        decipl   = dict[key][3]
        conv     = dict[key][4]
        try:
            sqlcolnm = dict[key][5]
        except IndexError:
            sqlcolnm = 'bogus'
        value = line[startpos:endpos]
        if conv in conversion.keys():
            func = conversion[conv]
            try:
                value = func(value.strip())
            except:
                # TODO: handle errors better/store bogus line
                # store: - error type
                #        - value
                #        - function
                #        - line
                print value
                print func
                print line
                print sqldict
                sys.exit(1)
        elif decipl:
            value = decimalise(value.strip(), decipl)
        else:
            pass
        sqldict[sqlcolnm] = value
    return sqldict


def write2table(sqldict, dict):
    """
    Take a dictionary containing column_name:value pairs and
    pass it to the appropriate sqlalchemy table object to be
    inserted into that table. 

    Do some sanity checking on the file header and footer 
    line/dictionary.

    sqldict can be a dictionary or a list of dictionaries
    
    """
    if dict==comtranscols:
        commission_infile_tbl.insert().execute(sqldict)
        return len(sqldict)
    elif dict==poltranscols:
        policy_infile_tbl.insert().execute(sqldict)
        return len(sqldict)
    elif dict==headcols:
        return 0
    elif dict==tailcols:
        return 0


def premium_type(str):
    return premium_types[str]

def premium_freq(str):
    return premium_freqs[str]

def sdsdate(datestr):
    if datestr:
        try:
            return time.strftime('%Y-%m-%d', time.strptime(datestr, '%Y%m%d'))
        except ValueError:
            return '0000-00-00'
    else:
        return '0000-00-00'

def yesterday(today):
    try:
        yd = time.mktime(time.strptime(today, '%Y%m%d'))-60*60*24*1
    except ValueError:
        yd = time.mktime(time.strptime(today, '%Y-%m-%d'))-60*60*24*1
    return time.strftime('%Y-%m-%d', time.localtime(yd))


def decimalise(string, dp):
    """
    Add a decimal place to a string of numbers.
    Put the minus sign in the correct position first if necessary.
    """
    div = Decimal(10**dp)
    if string.endswith('-'):
        string = '-%s' % (string[:-1],)
    elif string.endswith('+'):
        string = '%s' % (string[:-1],)
    num = Decimal(string)
    return num/div


def pickup(filetypeid=1):
    """
    Pickup and process input file.
    """
    return True


linetype = {
    '00': 'File Header',
    '10': 'Policy Transaction',
    '20': 'Commission Transaction',
    '99': 'File Trailer',
}

headcols = {
    0: ('Record Category', 0,  2, 0, 'c'),
    1: ('Source System',   2, 12, 0, 'c'),
    2: ('Cycle Number',   12, 17, 0, 'i'),
    3: ('Creation Date',  17, 25, 0, 'd'),
}

tailcols = {
    0: ('Record Category',                   0,  2, 0, 'c'),
    1: ('# Policy Transaction Records',      2, 12, 0, 'i'),
    2: ('# Commission Transaction Records', 12, 22, 0, 'i'),
}

poltranscols = {
    0:  ('Record Category',       0,   2, 0, 'c', 'record_category'),
    1:  ('Entity Type',           2,   5, 0, 'c', 'entity_type'),
    2:  ('Entity ID',             5,  35, 0, 'c', 'entity_id'),
    3:  ('Entity Version',       35,  49, 0, 'n', 'entity_version'),
    4:  ('Product Provider',     49,  59, 0, 'c', 'product_provider'),
    5:  ('Contract Number',      59,  79, 0, 'c', 'contract_number'),
    6:  ('Movement/Why Code',    79,  83, 0, 'c', 'movement_why_code'),
    7:  ('Effective Date',       83,  91, 0, 'd', 'effective_date'),
    8:  ('Value Effective Date', 91,  99, 0, 'd', 'value_effective_date'),
    9:  ('New Business Date',    99, 107, 0, 'd', 'new_business_date'),
    10: ('Entry Date',          107, 115, 0, 'd', 'entry_date'),
    11: ('Product Code',        115, 125, 0, 'c', 'product_code'),
    12: ('Product Instance',    125, 133, 0, 'c', 'product_instance'),
    13: ('Layer Type',          133, 137, 0, 'c', 'layer_type'),
    14: ('License Type',        137, 138, 0, 'n', 'license_type'),
    15: ('Investment Type',     138, 141, 0, 'c', 'investment_type'),
    16: ('Client Name',         141, 191, 0, 'c', 'client_name'),
    17: ('Scaling Factor',      191, 201, 5, 'n', 'scaling_factor'),
    18: ('Payment Manner',      201, 202, 0, 'c', 'payment_manner'),
    19: ('Premium Frequency',   202, 203, 0, 'n', 'premium_frequency'),
    20: ('Premium Term',        203, 205, 0, 'n', 'premium_term'),
    21: ('Premium Type',        205, 206, 0, 'n', 'premium_type'),
    22: ('Premium',             206, 221, 2, 'n', 'premium'),
    23: ('OMiPAY Reference ID', 221, 241, 0, 'c', 'omipay_reference_id'),
}

comtranscols = {
    0:  ('Record Category',       0,   2, 0, 'c', 'record_category'),
    1:  ('Comm. Transaction ID',  2,  42, 0, 'c', 'commission_transaction_id'),
    2:  ('Entity Type',          42,  45, 0, 'c', 'entity_type'),
    3:  ('Entity ID',            45,  75, 0, 'c', 'entity_id'),
    4:  ('Entity Version',       75,  89, 0, 'n', 'entity_version'),
    5:  ('Participation Type',   89,  90, 0, 'c', 'participation_type'),
    6:  ('Commission Contract',  90, 110, 0, 'c', 'commission_contract'),
    7:  ('Intermediary Type',   110, 111, 0, 'c', 'intermediary_type'),
    8:  ('Intermediary Code',   111, 117, 0, 'c', 'intermediary_code'),
    9:  ('Distribution Chan',   117, 119, 0, 'c', 'distribution_channel'),
    10: ('Commission Share %',  119, 129, 5, 'n', 'commission_share_percent'),
    11: ('Figure Share %',      129, 139, 5, 'n', 'figure_share_percent'),
    12: ('Sales Center Code',   139, 143, 0, 'c', 'sales_center_code'),
    13: ('Rem Type',            143, 147, 0, 'c', 'remuneration_type'),
    14: ('Rem Amount',          147, 162, 2, 'n', 'remuneration_amount'),
    15: ('Rem Currency',        162, 167, 0, 'c', 'remuneration_currency'),
    16: ('Rem Quantity',        167, 178, 2, 'n', 'remuneration_quantity'),
    17: ('Remuneration Unit',   178, 181, 0, 'c', 'remuneration_unit'),
    18: ('Due Date',            181, 189, 0, 'd', 'due_date'),
    19: ('Year Indicator',      189, 190, 0, 'c', 'year_indicator'),
    20: ('Period Assign. Date', 190, 198, 0, 'd', 'period_assignment_date'),
    21: ('OMiPAY Reference ID', 198, 218, 0, 'c', 'omipay_reference_id'),
    22: ('Rem Info Type',       218, 228, 0, 'c', 'reminfotype'),
}

premium_types = {
    'R': 'Recurring Premium',
    'G': 'Regular Premium',
    'S': 'Single Premium',
    'A': 'As and When',
    'F': 'Service Fee',
}

premium_freqs = {
    'M': 'Monthly',
    'Q': 'Quarterly',
    'H': 'Half Yearly',
    'Y': 'Yearly',
    'S': 'Single',
    '': 'Blank',
}

conversion = {
    'i': int,
    'f': float,
    'd': sdsdate,
    'pt': premium_type,
    'pf': premium_freq,
}

entity_types = {
    'DI': 'Due Item',
}

# channels
# NB: get Emerald from PFA
channel_codes = {
    '01': 'Personal Financial Advice',
    '02': 'Broker Distribution',
    '04': 'Private Wealth Management',
    '09': 'Franchise Channel',
}

products = {
    'max_focus': {
        'FOCUST':   ('Focussed Investment Plan LISP', 
                     'CINVTINV', 'Commit LISP'),
        'FOCUSINV': ('Focussed Investment Plan LIFE', 
                     'CINVINV', 'Commit Inv Pure LIFE'),
        'FOCUSRA':  ('Focussed Investment Plan RA', 
                     'CINVRA', 'Commit Inv RA LIFE'),
    },
    'max_flexible': {
        'FLEXT':   ('Flexible Investment Plan LISP', 
                    'SINVTINV', 'Select LISP'),
        'FLEXINV': ('Flexible Investment Plan LIFE', 
                    'SINVINV', 'Select Inv Pure LIFE'),
        'FLEXRA':  ('Flexible Investment Plan RA', 
                    'SINVRA', 'Select RA LIFE'),
    },
}

remtypes = {
    'pfa/pwm/em': {
        'BA12': ('Advice Fee (Core) - PFA', 'statistical'),
        'BC12': ('Commission (Core) - PFA', 'statistical'),
        'BP12': ('PUF Com (Core) - PFA', 'statistical'),
        'BP13': ('PUF Advice (Core) - PFA', 'statistical'),
        'BR31': ('Review Fee 1 (Core) - PFA', 'statistical'),
        'BR41': ('Review Fee 2 (Core) - PFA', 'statistical'),
    },
    'bd': {
        'A22': ('Advice Fee - BD', 'Direct'),
        'C22': ('Commission - BD', 'Direct'),
        'P22': ('PUF Comm - BD', 'Direct'),
        'P23': ('PUF Advice - BD', 'Direct'),
        'R322': ('Review Fee 1 BD', 'Direct'),
        'R422': ('Review Fee 2 BD', 'Direct'),
    },
    'af': {
        'A92': ('Advice Fee - Franchise', 'Direct'),
        'C92': ('Commission - Franchise', 'Direct'),
        'P92': ('PUF Comm - Franchise', 'Direct'),
        'P93': ('PUF Advice - Franchise', 'Direct'),
        'R392': ('Review Fee 1 - Franchise', 'Direct'),
        'R492': ('Review Fee 2 - Franchise', 'Direct'),
    },
}


reminfotypes = {
    '0001': ('Legal Maximum Commission', 
             'Statistical Remuneration Amount representing Legal Maximum Commission.'),
    '0003': ('Premium', 
             'Statistical Remuneration Amount representing Annualized Premium as used for incentive calculations.'), 
    '0004': ('SP Remuneration - Advice Fee - Upfront', 
             'Upfront Sales Person Remuneration Amount calculated according to Advice Fee rules.'), 
    '0005': ('SP Remuneration - Advice Fee - AAW', 
             'As-and-When Sales Person Remuneration Amount calculated according to Advice Fee rules.'),
    '0006': ('SP Remuneration - Legal Commission - Upfront', 
             'Upfront Sales Person Remuneration Amount calculated according to Legal Commission rules. '),
    '0007': ('SP Remuneration - Legal Commission - AAW', 
             'As-and-When Sales Person Remuneration Amount calculated according to Legal Commission rules. '),
    '0008': ('CH Remuneration - Advice Fee - Upfront', 
             'Upfront Channel Remuneration Amount calculated according to Advice Fee rules.'),
    '0009': ('CH Remuneration - Advice Fee - AAW', 
             'As-and-When Channel Remuneration Amount calculated according to Advice Fee rules.'),
    '0010': ('CH Remuneration - Legal Commission - Upfront', 
             'Upfront Channel Remuneration Amount calculated according to Legal Commission rules.'),
    '0011': ('CH Remuneration - Legal Commission - AAW', 
             'As-and-When Channel Remuneration Amount calculated according to Legal Commission rules.'),
    '0012': ('SP Remuneration - Legal Commission - Asset Fee', 
             'Monthly Asset Fee if remuneration is calculated according to Legal Commission rules.'),
    '0013': ('SP Remuneration - Advice Fee - Asset Fee', 
             'Monthly Asset Fee is remuneration is calculated according to Advice Fee rules.'),
    '0014': ('SP Remuneration - Advice Fee - Advanced', 
             'Advanced upfront Sales Person Remuneration Amount calculated according to Advice Fee rules.'),
    '0015': ('SP Remuneration - Legal Commission - Advanced', 
             'Advanced upfront Sales Person Remuneration Amount calculated according to Legal Comm. rules.'),
}
