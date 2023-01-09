#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
support code is non-class general manipulation functions

@author: Crumbs
"""
import glob
import os
from urllib.parse import urlparse
import re


def addr_newest(file_use, file_path=None):
    """ given file_use use find the newest json file in the same path with
        the same starting name
        
        some_name.<anything>.json
        
        which means it returns the newest some_name.*.json file
        meant to match the latest timestamped book where anthing is the time
        
    Args:
        file_use (str): reference name for file
            if file_path is not specified it must be an absolute path
        file_path (str): file_path to search, if None pulls from file_use
            default=None
    Returns:
        (str): newest file that matches the file_use pattern
            if no matching files are found it returns None
    """
    file_use_base = os.path.basename(file_use).split('.')[0]
    if file_path is None:
        file_path = os.path.dirname(file_use)
    files = glob.glob(
        os.path.join(file_path, f'{file_use_base}*.json'),
        recursive=True)
    # return the newest file by ctime in the set of files
    if len(files) > 0:
        return max(files, key = os.path.getctime)
    else:
        return None


def field_to_list(field):
    """give a field, presumably str, convert to list dropping '' and None values
    
    Args:
        field (*): value to convert, expect string but can put anything
            into a list
    Returns:
        either input as list or if input = '' or None return []
        field if type(field) is list
        []  if input is '' or None
        [field] otherwise
    """
    if type(field) is list:
        fieldaslist = []
        for fieldx in field:
            if fieldx is None:
                continue
            if type(fieldx) is str and fieldx == '':
                continue
            fieldaslist.append(fieldx)
        return fieldaslist
    
    if field is None:
        fieldaslist = []
    elif type(field) is str:
        if len(field) == 0:
            fieldaslist = []
        else:
            fieldaslist = [field]
    else:
        fieldaslist = [field]
    return fieldaslist


def file_read_file_location_mod(mod_file, mod_dict={}):
    """
    read the file that lists by file location modification lookups
    note: file location is the file dirname w/o leading common drive folders 
    
    file format:
            new_label\tfile location
    previously known to be saved to:
        os.path.join(output_path, 'location_set_mapping.tab')

    Args:
        mod_file (str): filename path to location_set_mapping.tab
        mod_dict (dict): the modification dictionary to add the content read
            from the file to; directory vs file location label
    Returns:
        mod_dict (dict) whose keys are addresses and values are a label list
    """
    with open(mod_file) as fHan:
        file_loc_mod_lines = fHan.readlines()
    
        for line in file_loc_mod_lines:
            try:
                line = line.strip('\n')
                new_label, loc_to_mod = line.split('\t')
            except ValueError:  # occurs if line above is improperly formatted
                continue
            mod_dict[loc_to_mod] = [new_label]
       
    return(mod_dict)


def file_read_label_mod_by_addr(mod_file, mod_dict={}):
    """
    read the file that lists by url addr lookups to change the label
    file format:
            addr_url\tlabel
            addr_url\tlabel1:::label2
    previously known to be saved to:
        os.path.join(output_path, 'duplicate_addr_labels.tab')

    Args:
        mod_file (str): filename path to duplicate_addr_labels.tab
        mod_dict (dict): the modification dictionary to add the content read
            from the file to
    Returns:
        mod_dict (dict) whose keys are addresses and values are a label list
    """
    with open(mod_file) as fHan:
        addr_mod_lines = fHan.readlines()
    
        multi_label = re.compile(':::')
        for index, line in enumerate(addr_mod_lines):
            try:
                line = line.strip('\n')
                addr_to_mod, new_label = line.split('\t')
            except ValueError:  # occurs if line above is improperly formatted
                continue
            if multi_label.match(new_label) is not None:
                 new_labels = new_label.split(':::')
                 mod_dict[addr_to_mod] = new_labels
            else:
                mod_dict[addr_to_mod] = [new_label]
    return(mod_dict)


def is_url(text):
    """ check input text is url or not

    Args:
        text (str): input text
    Return:
        (boolean) url or not
    """
    parsed = urlparse(text)
    return all([parsed.scheme, parsed.netloc, parsed.path])


def reduce_filename(filename, drop_str=['bookmarks']):
    """
    given a filename return the basename without dated content or extension
    dated content in following formats stripped:
        YYYYMMDD format ie 8 consecutive digits
        YYYY-MM-DD
        HH-MM-SS
        YYYY-MM-DD_HH-MM-SS
    if after strip only non-alphabet characters remain output set to ''
    Remove duplicate -- and __ to single value
    
    this function is used to reduce the number of file locations because will
    have occur multiple times due to date, when just want context of source    

    Args:
        filename (str): filename string
        drop_str (list): list of strings to remove from the filename
    Returns:
        (str) or if input filename is not str returns passed object
    """
    if type(filename) is not str:
        return(filename)
    # get basename without extension
    x = os.path.basename(filename)
    x = os.path.splitext(x)[0]
    # drop strings
    for dropStr in drop_str:
        x = x.replace(dropStr,'')
    # drop date content YYYYMMDD[a-zA-Z] for case like* 20090724a.html
    date_find = re.search('[0-9]{8,8}[A-Za-z]$', x)
    if date_find is not None:
        # date_find = date_find.span()
        x = x.replace(date_find[0], '')
    # drop date content YYYYMMDD
    date_find = re.search('[0-9]{8,8}', x)
    if date_find is not None:
        # date_find = date_find.span()
        x = x.replace(date_find[0], '')
    # drop date content YYYY-MM-DD which also reduces YYYY-MM-DD_HH-MM-SS
    date_find = re.search('[0-9]{4,4}-[0-9]{2,2}-[0-9]{2,2}', x)
    if date_find is not None:
        # date_find = date_find.span()
        x = x.replace(date_find[0], '')
    # drop hour content from previously modified YYYY-MM-DD_HH-MM-SS
    date_find = re.search('[0-9]{2,2}-[0-9]{2,2}-[0-9]{2,2}', x)
    if date_find is not None:
        # date_find = date_find.span()
        x = x.replace(date_find[0], '')
    if len(x) > 0:
        alphabet_find = re.search('[A-Za-z]', x)
        if alphabet_find is None:
            # no words found; strip output
            x = ''
        else:
            while re.search('__', x) is not None:
                x = x.replace('__', '_')
            while re.search('--', x) is not None:
                x = x.replace('--', '-')
    # strip output of leading and trailing characters
    x = x.strip('_- .')
    return (x)