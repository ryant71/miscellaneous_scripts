#!/usr/bin/env python

import sys
import hashlib
import zipfile

from lxml import etree
from StringIO import StringIO


def usage():
    usage = (
        'Usage: %s options\n'
        ' Options:\n'
        '  <war/jar>                    prints jdbc source, context if applicable\n'
        '  <war/jar> -sha               print jar/war contents plus sha1 of each file\n'
        '  <war/jar> -list              print jar/war contents\n'
        '  <war/jar> -showconfigs       print contents of config files with war/jar\n'
        '  <war/jar> <filepath>         print contents of <filepath> within war/jar\n'
        '  <war/jar> <filepath(.jar)>   print contents of jar within war/jar\n'
        '  <war/jar> <filepath(.jar)> <filepath>\n'
        '                               print contents of file within jar within war/jar\n')
    print(usage)
    sys.exit()


def is_file(filepath):
    filename = filepath.split('/')[-1]
    if not filename:
        return None
    else:
        return filepath


def is_config_filename(filepath):
    filename = filepath.split('/')[-1]
    if not filename:
        return None
    elif filename.find('.pom') >= 0:
        return filepath
    elif filename.find('.xml') >= 0:
        return filepath
    elif filename.find('.properties') >= 0:
        return filepath
    else:
        return None


def is_jar(filepath):
    filename = filepath.split('/')[-1]
    if filename.find('.jar') >= 0:
        return filename
    else:
        return None


def get_common_file(filenames, filepaths, searchfile):
    for filename in filenames:
        if filename.find(searchfile) >= 0:
            # print(filename)
            for filepath in filepaths:
                if filepath.find(filename) > 0:
                    # print(filepath)
                    return (filename, filepath)
    return (None, None)


def get_inner_zip(zipobject, filepath):
    innerzip = StringIO(zipobject.read(filepath))
    return zipfile.ZipFile(innerzip)


def get_file_contents(zipobject, filepath):
    try:
        return zipobject.open(filepath).read()
    except KeyError:
        return None


def get_sha1(filecontents):
    return hashlib.sha1(filecontents).hexdigest()


def find_file(zipobj, file):
    files = zipobj.namelist()
    for filepath in files:
        filename = filepath.split('/')[-1]
        if filename == file:
            return (filename, filepath)
    return (None, None)

"""
xml:
hibernate-configuration session-factory property (name = connection.datasource)
"""


def get_connection_datasource(xmlstring):
    xmlobject = etree.XML(xmlstring)
    properties = xmlobject.xpath(
        '//hibernate-configuration//session-factory//property')
    for prop in properties:
        if prop.attrib['name'] == 'connection.datasource':
            return prop.text


def get_jndi_name(xmlstring):
    xmlobject = etree.XML(xmlstring)
    try:
        datasources = xmlobject.xpath(
            '//glassfish-web-app//resource-ref//jndi-name')
        datasources = [ds.text for ds in datasources]
    except IndexError:
        datasources = None
    return datasources


def get_context_root(xmlstring):
    xmlobject = etree.XML(xmlstring)
    try:
        return xmlobject.xpath('//glassfish-web-app//context-root')[0].text
    except IndexError:
        return None

"""
TokenCommon-1.0.0.jar
cvs-common-x.x.x.jar
"""

if __name__ == "__main__":

    if '-sha' in sys.argv:
        do_sha = True
        sys.argv.remove('-sha')
    else:
        do_sha = False

    if '-list' in sys.argv:
        do_list = True
    else:
        do_list = False

    if '-showconfigs' in sys.argv:
        do_showconfigs = True
    else:
        do_showconfigs = False

    if '-h' in sys.argv:
        usage()

    try:
        zf = zipfile.ZipFile(sys.argv[1], 'r')
    except (IOError, IndexError):
        usage()

    try:
        printfile = sys.argv[2]
    except IndexError:
        printfile = None

    filepaths = zf.namelist()
    filesonly = [is_file(filepath)
                 for filepath in filepaths if is_file(filepath)]
    configfilenames = [is_config_filename(
        filepath) for filepath in filepaths if is_config_filename(filepath)]
    jarfiles = [is_jar(filepath) for filepath in filepaths if is_jar(filepath)]

    if do_sha:
        for filepath in filesonly:
            sha1 = get_sha1(get_file_contents(zf, filepath))
            print('%s %s' % (sha1, filepath))

    if do_list:
        for filepath in filesonly:
            print('%s' % (filepath,))

    xml = get_file_contents(zf, find_file(zf, 'hibernate.cfg.xml')[1])
    if xml:
        datasource = get_connection_datasource(xml)
        print('Base War: ')
        print(' File: hibernate.cfg.xml')
        print(' Datasource: %s \n' % datasource)

    if do_showconfigs:
        for file in configfilenames:
            print('######### config file = %s ########' % file)
            print(get_file_contents(zf, file))
            print('')

    # ----begin blecch----
    # make this more generic - search for hibernate.cfg.xml in all jars, maybe?
    for searchfile in ['TokenCommon', 'cvs-common']:
        sfilename, sfilepath = get_common_file(jarfiles, filepaths, searchfile)

        if sfilename and sfilepath:

            commonzip = get_inner_zip(zf, sfilepath)
            xml = get_file_contents(commonzip, 'hibernate.cfg.xml')
            datasource = get_connection_datasource(xml)
            print('Config Jar: %s' % sfilename)
            print(' File: hibernate.cfg.xml')
            print(' Datasource: %s ' % datasource)

    xmlstring = get_file_contents(zf, 'WEB-INF/glassfish-web.xml')
    if xmlstring:
        datasources = get_jndi_name(xmlstring)
        contextroot = get_context_root(xmlstring)
        print('File: WEB-INF/glassfish-web.xml')
        if datasources:
            for ds in datasources:
                print('Datasource: %s ' % ds)
        if contextroot:
            print('Context: %s ' % contextroot)
    # ----end blecch----

    if printfile:
        if is_jar(printfile):
            inner_zip_obj = get_inner_zip(zf, printfile)
            _filepaths = inner_zip_obj.namelist()
            _filepaths = [is_file(fp) for fp in _filepaths if is_file(fp)]
            try:
                deepfile = sys.argv[3]
            except IndexError:
                deepfile = None
            if deepfile:
                print(get_file_contents(inner_zip_obj, deepfile))
            else:
                print('%s:' % printfile)
                for fp in _filepaths:
                    sha1 = get_sha1(get_file_contents(inner_zip_obj, fp))
                    print('\t%s %s' % (sha1, fp))
        else:
            print(get_file_contents(zf, printfile))
