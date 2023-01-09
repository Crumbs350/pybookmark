#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
use bookmarks_parse.py to merge many different bookmark files

creates output files:
    duplicate_addr_descriptions.txt     url, description:::descriptionN csv
    duplicate_addr_locations.txt        url, location:::locationN csv
    duplicate_addr_locations_flat.txt   duplicate locations w/ no links
    duplicate_addr_location_sets.txt    duplicate locations linked as tuple
    duplicate_addr_labels.txt           url, label:::labelN csv
                                            use file to update .tab version
    merge_process_failed.txt            html files that failed to import
    addr_original.json                  addrStruct exported right after merge
    addr.json                           addrStruct reduced
    
input files used to modify/reduce bookmark sets:
    duplicate_addr_labels.tab           duplicate label mapping
                                        read by bp.file_read_label_mod_by_addr()
    location_set_mapping.tab            file that lists by file location modification lookups
                                        read by bp.file_read_file_location_mod()
    data/bookmarks_merge.yaml           some configuration variables are mappings

structure of the created final merged json file is a dictionary
    key = URL
    value = list of following
        label (list): descriptive label for the URL
        age (int): when it was created
        tags (list)
        location (list): 
        description (list): descriptive comments to add context to URL
        file location (list): list of where this link was found, source files

examples:
    $ python bookmarks_merge.py /data_dir /data_dir/bookmarks_merged/

    # using yaml configuration for how to reduce bookmarks
    $ python bookmarks_merge.py -y data/bookmark_merge.yaml /data_dir /data_dir/bookmarks_merged/

caveats:
    Do not name any html output as with bookmark in the name
    Do not run on more than a few files in spyder it is much faster in console
    
    'Requires' duplicate_addr_labels.tab file to exist in the output path
        code can ignore it not existing now.
        file is created from duplicate_addr_labels.txt

@author: Crumbs
"""

import argparse
import yaml

# ref: https://stackoverflow.com/questions/8804830/python-multiprocessing-picklingerror-cant-pickle-type-function
from multiprocessing import cpu_count
import os
import pandas as pd
import re
import sys
import time

sys.path.append(os.path.dirname(__file__))
import pybookmark.bookmarks_parse as bp
import pybookmark.bookmarks_class as bc
import pybookmark.support as support
from pybookmark.pybookmarkjsonviewer import get_time_str

# if above fails run following because it thinks path bookmarks_parse is the package
#   from bookmarks_parse import bookmarks_parse as bp


def len_unique(x):
    """ intended to be called by pd.DataFrame.apply
    returns the length of the unique list for the series passed
    
    Args:
        x (pd.Series)
    Returns:
        (int)
    """
    return len(pd.unique(x))
    

if __name__ == '__main__':
    # - handle inputs
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('-d', '--debug', dest='debug', 
                        required=False, action='store_true',
                        help='call to set debug mode; hardcoded paths')
    parser.add_argument('file_path', 
                        type=str,
                        help='file path for bookmarks.html files.' +\
                            'used as default output_path if not defined otherwise')
    parser.add_argument('-m', '--multiprocessors', dest='nprocesses',
                        required=False, 
                        help='Integer. If set uses N processes. Else 1' +\
                            'Code checks and forces max processes to CPU-1' +\
                            'Currently does not work due to underling code')
    parser.add_argument('output',
                        type=str,
                        help='''file path for output file
                                if absent uses path of input file
                                value can be overwritten by the yaml
                                output_path configuration value.''')
    parser.add_argument('-j', '--json', dest='json_file',
                        required=False, 
                        help='''Existing addr.json file to join new information
                            to. File is read and passed to bp.buildAddressStruct
                            import existing bookmarks then only search a
                            a small subset of the new bookmarks to add. Value
                            overwritten by yaml output_file configuration value.''')
    parser.add_argument('-t', dest='timestamp_no',
                        required=False, 
                        action='store_true',
                        help='''If set do not timestamp.''')
    parser.add_argument('-y', '--config', type=str, default=None,
                        help='yaml config file path for modification variables.')
                        
    script_name = os.path.basename(__file__)
    args = parser.parse_args()
    debug = args.debug
    file_path = args.file_path

    sys.setrecursionlimit(10000)    # this really needs to expand as necessary
        # gets stuck on some files. therefore disabled
        # 3000 did not work for newer files from datamonster for unknown reasons

    # define paths (can be overwritten by yaml)
    if args.output is None:
        output_path = file_path
    else:
        output_path = args.output
    
    output_file_basename = 'addr.json'

    # 
    # externally configurable parameters to fix (define empty so they exist)
    #
    # - locations element [3]
    # for each address reduce location set by: replace, reduce, & drop
    # replaceStringsAll (list of lists) where 0 is match pattern and 1 element is the replace string
    replaceStringsAll = []
    # dropSetLeading (list) strings to match at the beginning of the element, matches are removed
    dropSetLeading = []
    # replaceStringsFirst (list of lists) where 0 is match pattern and 1 element is the replace string
    #    action applied: change the replacement string then remove leading ::
    replaceStringsFirst = []
    # - description element [4]
    # list of urls to define description list as original description split on \n
    desc_join_addrs = []
    # dictionary of key = url, value = description list to use
    desc_dup_mod = {}
    # values to remove from list values
    emptyContentDropSet = []

    ncpu = 1
    if args.nprocesses is not None:
        ncpu = min(int(args.nprocesses), cpu_count()-1)

    if args.config:
        config_f = args.config
        # use yaml instead of passed arguments, assumed in current path
        assert os.path.exists(config_f) # user intended use so bail if not found

        with open(config_f, 'r') as fHan:
            config_args = yaml.safe_load(fHan)
                
        # overwrite local variable definitions with 
        if 'replaceStringsAll' in config_args:
            replaceStringsAll = config_args['replaceStringsAll']
        if 'dropSetLeading' in config_args:
            dropSetLeading = config_args['dropSetLeading']
        if 'replaceStringsFirst' in config_args:
            replaceStringsFirst = config_args['replaceStringsFirst']
        if 'desc_join_addrs' in config_args:
            desc_join_addrs = config_args['desc_join_addrs']
        if 'desc_dup_mod' in config_args:
            desc_dup_mod = config_args['desc_dup_mod']
        if 'emptyContentDropSet' in config_args:
            emptyContentDropSet = config_args['emptyContentDropSet']
        if 'output_path' in config_args:
            # not this overides expected behavior
            output_path = config_args['output_path']
        if 'emptyContentDropSet' in config_args:
            emptyContentDropSet = config_args['emptyContentDropSet']
        if 'output_file' in config_args:
            output_file_basename = config_args['output_file']

    # - handle paths
    assert os.path.exists(file_path) # the input data path must exist

    if not os.path.exists(output_path):
        print('Defined output_path does not exist, create it.')
        os.makedirs(output_path)

    # - import existing json structure to append to
    if (args.json_file is not None) and os.path.exists(args.json_file):
        addrStruct = bc.bookmarks.Address_Struct_Read(args.json_file)
        if len(addrStruct) > 0:
            print(f'Read {len(addrStruct)} urls from {args.json_file}')
    else:
        addrStruct = bc.bookmarks()
   
    # - run code to merge the bookmarks found in the input file_path
    print('Start reading input path')
    t1 = time.time()
    addresses, file_ages, bad_files = bp.parse_path(file_path, ncpu=ncpu)
    t2 = time.time()
    print(f'{script_name} parse time for {len(file_ages)} files = {t2-t1} seconds')
    print(f'encountered {len(bad_files)} bad files')
    
    with open(os.path.join(output_path, 'merge_process_failed.txt'), 'wt') as fHan:
        for bad_file in bad_files:
            fHan.write(bad_file + '\n')
    
    # addresses definition
    #   [0] = label (did call description before)
    #   [1] = url
    #   [2] = age
    #   [6] = tags
    #   [7] = location
    #   [8] = file or description if 10 elements
    #   [9] = file if 10 elements
    
    if debug:
        # get the unique set of unaltered address locations
        addrloc = {}
        for addrlist in addresses:
            addr_loc = addrlist[7].strip()
            addrloc[addr_loc] = 1
        
        with open(os.path.join(output_path, 'addr_locations.txt'), 'wt') as fHan:
            for addr_loc in sorted(addrloc.keys()):
                fHan.write(addr_loc + '\n')
    
    # build dictionary by address and list data structure
    # merges but does not clean the data
    addrStruct.build_address_struct(addresses)
        # key = addr
        # [0] = label
        # [1] = age
        # [2] = tags
        # [3] = location
        # [4] = description
        # [5] = file location
    
    print(f'set of unique addresses: {len(addrStruct)}')

    # create _original name and save unaltered address set to it
    file_parts = list(os.path.splitext(output_file_basename))
    
    if not args.timestamp_no:
        # add a timestamp (modifies basename)
        file_parts1 = file_parts.copy()
        file_parts1[0] = f'{file_parts1[0]}.{get_time_str()}'
        output_file_basename = ''.join(file_parts1)
        file_parts[0] = f'{file_parts[0]}_original.{get_time_str()}'
    else:
        # no timestamp
        file_parts[0] = file_parts[0] + '_original'
    output_file_original = ''.join(file_parts)
    addrStruct.bc.write_json(os.path.join(output_path, output_file_original))

    #
    # YYY: below this point need to remove all parse_html output variables
    #       ie only manipulate the addrStruct
    #
    #   propogating the above structure changes through the code below
    #   addr_dict_loc from before is now addrStruct[addr_url][3] to get list of locations
    #
    #   YYY: search for an address:
    #      list(filter(lambda x: re.search('bluehighway', x), addrStruct.keys()))
    
    # now need to compare and merge them; can use address and file timestamp
    # same url then add another works column?
    
    # YYY: need to go through the output duplicate files, identify the ones
    #   that should have been matched, check loaded original addr struct
    #   to avoid issues with searching for 'x y' when should be 'x_y'
    #
    #   x = bp.searchAddressStruct(addrStruct, '2read_then_sort', 3)
    #   bp.searchAddressStructPrint(addrStruct, x, 3)
    
    #-------------------------------------------------------------------------
    # - locations element [3]
    #-------------------------------------------------------------------------
    
    # - for each address reduce location set by: replace, reduce, & drop
    for addr_key in addrStruct.keys(): # modifying [3] the locations
        reduced = addrStruct[addr_key].get_value('location')  #[3] 
        
        # reduce list length to search by using set, replacing existing list
        if len(addrStruct[addr_key].get_value('location')) > 0:
            # remove the leading and trailing whitespace + reduce to unique
            # this also removes None values preventing errors below
            reduced = list(set([x.strip() for x in reduced if x is not None]))
        else:
            continue    # zero length so nothing to change

        # reduce duplicate locations by dropping irrelevant locations
        if 'Bookmarks Menu' in reduced:
            reduced = list(filter(lambda x: x != 'Bookmarks Menu', reduced))
            
        # modify the strings to reduce levels and map similar items to the same structure
        #   QQQ: can replaceStringsAll and replaceStringsFirst be merged by changing
        #       this to use .sub = replace left most vs .replace = all
        # while not required good practice to consistently remove leading :: 
        #   so successive start of string matches work
        for replaceString in replaceStringsAll:
            reduced = [re.sub('^::', '', 
                              x.replace(replaceString[0], replaceString[1])) for x in reduced]
                        
        # remove the parent folder locations, this drops where information
        #   is where relevant?
        #   provides context, does it matter or just increase complexity?
        #   increases complexity therefore drop.
        #   dropSetLeading hardcoded is not an input file on purpose
        
        # because dropSetLeading matches at start all preceeding removals (ie dropSetLeading)
        #   must have a trailing :: or remove leading colons between removeStr
        for removeStr in dropSetLeading:
            # remove the drop string start item then
            # remove leading :: so successive start of string matches work
            reduced = [re.sub('^::', '',
                              re.sub(f'^{removeStr}', '', x, count=1)) for x in reduced]
            
        # leading category prepend
        for replaceString in replaceStringsFirst:
            # change the replacement string then remove leading :: 
            reduced = [re.sub('^::', '',
                              re.sub(replaceString[0], replaceString[1],
                                     x, count=1)) for x in reduced]
        
        # remove _ so all are space based and strip because of prior mods
        # QQQ: do the spaces in replace strings above need to be replaced with _?
        reduced = [re.sub('_', ' ', x).strip() for x in reduced]

        if len(reduced) > 1:
            # reduce list length to search by using set, replacing existing list
            reduced = list(set(reduced))
                        
            # - drop locations that are a subset of other location strings
            # first build up the list of string subsets
            subStringDropI = []
            for i in range(len(reduced)):
                if i in subStringDropI:
                    continue
                locNow = reduced[i] + '::'
                for j in range(len(reduced)):
                    if i == j:
                        continue
                    locComp = reduced[j]
                    if locComp.find(locNow, 0) != -1:
                        # match found, mark the substring and stop comparing
                        # print(f'{locNow}  {locComp}')
                        subStringDropI.append(i)
                        break
                    # match not found drop :: and search at the end?
                    #   no lazy match mod the comparison to get to end
                    #   otherwise must take length and assign start and stop
                    # problem: works but matches short words like radio to stl_radio
                    #   and only removes about 150 multi-address items
#                    locComp = locComp + '::'
#                    if locComp.find(locNow, 0) != -1:
#                        print(f'end match {locNow}  {locComp}')
#                        subStringDropI.append(i)
#                        break
            # if string subsets exist, drop them
            if len(subStringDropI) > 0:
                reduced = [
                        reduced[dropi] for dropi in 
                            set(range(len(reduced))).
                             difference(set(subStringDropI)) ]
            # remove empty strings
            reduced = [x for x in reduced if len(x) > 0]
            
            # QQQ how to handle lower vs upper case variants? sometimes typos other times want to know
             
        # prevent zero-length list
        if len(reduced) == 0:
            reduced = ['']
        
        # update the data element
        addrStruct[addr_key].set_value('location', reduced, overwrite=True)
    
    # - do duplicate locations still exist?
    with open(os.path.join(output_path, 'duplicate_addr_locations.txt'), 'wt') as fHan:
        dupCount = 0
        for addr_key in addrStruct.keys():
            if len(addrStruct[addr_key].get_value('location')) > 1:
                dupCount = dupCount + 1  # count number of duplicated addresses
                # write out the addresses and unique set of locations
                fHan.write(addr_key 
                           + ', '
                           + ':::'.join(list(set(addrStruct[addr_key].get_value('location'))))
                           +'\n')
    print(f'Still have {dupCount} addresses with multiple locations')
    
    # - generate and write out the set of possible locations
    loc_list = []       # all locations
    loc_dup_list = []   # duplicate locations
    loc_dup_set = set() # set of duplicate location groups
    for addr_key in addrStruct.keys():
        loc_now = addrStruct[addr_key].get_value('location')   #[3]
        loc_list = loc_list + loc_now
        if len(loc_now) > 1:
            loc_now.sort()  # so tuples below match
            loc_dup_list = loc_dup_list + loc_now
            loc_dup_set.add(tuple(loc_now))  # set of location lists

    print('set of locations:', len(loc_list))
    loc_list = list(set(loc_list))
    print('set of locations reduced:', len(loc_list))
    print('set of location duplicates:', len(loc_dup_list))
    loc_dup_list = list(set(loc_dup_list))
    print('set of location duplicates reduced:', len(loc_dup_list))
    print('number of location set duplicates:', len(loc_dup_set))
    
    with open(os.path.join(output_path, 'duplicate_addr_locations_flat.txt'), 'wt') as fHan:
        for addr_loc in loc_dup_list:
            fHan.write(addr_loc + '\n')
    
    loc_dup_set_list = list(loc_dup_set)
    loc_dup_set_list.sort()
    
    with open(os.path.join(output_path, 'duplicate_addr_location_sets.txt'), 'wt') as fHan:
        for dup_set_i in loc_dup_set_list:
            fHan.write(f'{dup_set_i}\n')
    
    #-------------------------------------------------------------------------
    # - label element [0]
    #-------------------------------------------------------------------------
    
    #
    # -- handle duplication of labels
    #
    # if file doesn't exist do not read or reduce duplication by mod_file matches
    # if file exists read and reduce duplication in addrStruct
    # write out remaining duplication text file (dup_file)
    #
    #   then modify all code references
    mod_file = os.path.join(output_path, 'duplicate_addr_labels.tab')
    dup_file = os.path.join(output_path, 'duplicate_addr_labels.txt')

    addr_label_mod_dict = {}
    if os.path.exists(mod_file):
        # - mod_file exists so can read and apply to reduce duplication
        addr_label_mod_dict = bp.file_read_label_mod_by_addr(mod_file, addr_label_mod_dict)
        
        # change duplicate labels by url to a single label, 
        #   for urls in addr_label_mod_dict replace all labels with a 
        #   single previously defined label
        for addr in addr_label_mod_dict:    # assume mod_dict is smaller than addrStruct
            if addr in addrStruct:
                addrStruct[addr].set_value('label', addr_label_mod_dict[addr], overwrite=True)
                # code below replaces all individually (ie duplicate definitions)
                # for alabi,alabn in enumerate(addrStruct[addr][0]):
                #    addrStruct[addr][0][alabi] = addr_label_mod_dict[addr]
    
    # - build up and export the set of labels by url; 
    # eventually used to create/update duplicate_addr_labels.tab
    # code does not add in existing addr_label_mod_dict definitions
    addr_dict2 = {}  # the set of duplicate addresses
    for addr in addrStruct:
        if len(addrStruct[addr].get_value('label')) > 0:
            # remove the leading and trailing whitespace
            if type(addrStruct[addr].get_value('label')) is str:
                # this should not happen; fix it
                print(f'addrStruct label str fixed: {addr}')
                addrStruct[addr].set_value(
                    'label', 
                    [(addrStruct[addr].get_value('label')).strip()],
                    overwrite=True)
            else:
                reduced = list(set([x.strip() for x in addrStruct[addr].get_value('label') if x is not None]))
                addrStruct[addr].set_value('label', reduced, overwrite=True)
        # by using addrStruct not addresses must account for possible lists
        # in label and descriptions
        addr_label = addrStruct[addr].get_value('label')
        if len(addr_label) > 1:
            addr_dict2[addr] = addr_label

    # count number of duplicated addresses that will be exported to txt for review
    dupCount = len(addr_dict2) 
    if dupCount > 0:
        print(f'{dupCount} unique addresses have duplicate descriptions.')
    
    # note: was previously called duplicate_addr_descriptions.txt
    #   use this output file to identify duplicates then append the 
    #   address and label definitions to duplicate_addr_labels.tab
    with open(dup_file, 'wt') as fHan:
        for addr_key in addr_dict2.keys():
            # write out the addresses and unique set of labels
            fHan.write(addr_key 
                       + ', '
                       + ':::'.join(list(set(addr_dict2[addr_key])))
                       +'\n')

    #-------------------------------------------------------------------------
    # - description element [4]
    #-------------------------------------------------------------------------
    
    # - for specific marked url addresses replace the description the unique
    #   set of all descriptions separated by \n
    #   ie assume original description elements are \n separated
    #   could make dictionary url:separator but only know to apply to 1 file
    for addr in desc_join_addrs: 
        desc_joined = []
        if addr not in addrStruct:
            continue
        for descn in addrStruct[addr].get_value('description'): # [4]:
            desc_joined = desc_joined + descn.split('\n')
        addrStruct[addr].set_value('description',
                                   ['\n'.join(list(set(desc_joined)))],
                                   overwrite=True)
      
    # - reduce descriptions by applying bp.file_read_desc_mod_by_addr() output moved to the yaml file
    for addr in desc_dup_mod.keys():
        if debug:
            print(f'{addr}:::{desc_dup_mod[addr][0:10]}')
        if addr in addrStruct:
            addrStruct[addr].set_value('description', desc_dup_mod[addr], overwrite=True)
            
    # - reduce to the unique set of descriptions irrespective of order
    #   also cleans descriptions of leading/trailing spaces
    # - reduce the descriptions retaining order and stripping leading/trailing spaces and newlines
    for addr in addrStruct:
        if len(addrStruct[addr].get_value('description')) > 0:
            reduced = list(set([x.strip().strip('\n') for x in addrStruct[addr].get_value('description') if x is not None]))
            addrStruct[addr].set_value('description', reduced, overwrite=True)

    # - which addresses still have multiple descriptions?
    # XXX: after exporting to duplicate_addr_descriptions need to use it to manually update
    #       the yaml file to reduce the description, ie desc_dup_mod key
    #       could also generate bp.file_read_desc_mod_by_addr() but seems unnecessary
    with open(os.path.join(output_path, 'duplicate_addr_descriptions.txt'), 'wt') as fHan:
        for addr in addrStruct:
            if len(addrStruct[addr].get_value('description')) > 1:
                fHan.write(addr 
                       + ', '
                       + ':::'.join(addrStruct[addr].get_value('description'))
                       +'\n')    
    
    #-------------------------------------------------------------------------
    # - file location element [5]
    #-------------------------------------------------------------------------
    
    # - figure out how to drop the common paths to reduce storage cost
    #   how many folders to drop from the start of the path?
    #   identify by collecting and splitting all paths, then computing
    #   the unique number of folder names at the path level using pandas
    paths = []
    for addr in addrStruct:
        for path_now in addrStruct[addr].get_value('file location'): #[5]:
            path_now = os.path.dirname(path_now)
            if not(path_now in paths):
                paths.append(path_now)
    paths2 = [path_now.split(os.path.sep) for path_now in paths]
    pathDF = pd.DataFrame(paths2)
    column_unique = pathDF.apply(len_unique, 0, False)  # apply to columns 
    drop_count = 0
    print('Paths to be dropped from the start of file sources:')
    for col_i, x in enumerate(column_unique):
        #if drop_count == 0 and len(pathDF.iloc[0, col_i]) == 0:
        #    # skips empty strings, zero length lead item
        #    continue
        if x == 1:
            drop_count += 1
        else:
            break
        print(f'\t{pathDF.iloc[0, col_i]}')
        
    # drop the leading common path elements
    # YYY: drop_count will have to be manually provided for addrStruct updates
    #   if handled separate from the code
    for addr in addrStruct:
        addrStruct[addr].set_value('file location', [
            (os.path.sep).join(path_now.split(os.path.sep)[drop_count:]) 
            for path_now in addrStruct[addr].get_value('file location')],
            overwrite=True)

    # - reduce the file locations to the unique set using 
    #   support.reduce_filename to get file basename reduced 
    #   and location_set_mapping.tab dictionary to reduce paths
    loc_label_file = os.path.join(output_path, 'location_set_mapping.tab')
    loc_label_dict = {}
    if os.path.exists(loc_label_file):
        # - location mod_file exists so can read and apply to simplify file locations
        loc_label_dict = bp.file_read_file_location_mod(loc_label_file, loc_label_dict)
    for addr in addrStruct:
        path_list = []
        for pathn in addrStruct[addr].get_value('file location'):
            # this joins 2 types of file location reduction into 1 value per path
            fbprf = support.reduce_filename(pathn)   # this is a single value
            pathn_dir = os.path.dirname(pathn)
            if pathn_dir in loc_label_dict:
                for pathn2 in loc_label_dict[pathn_dir]:
                    path_list.append(f'{pathn2}:::{fbprf}')
        addrStruct[addr].set_value('file location', 
                                   list(set(path_list)),  # reduce to unique and write
                                   overwrite=True)
    # YYY: note the file location is so mangled by de-duplication that 
    #   an output file can not be generated from here to help in removing
    #   duplicate information but rather the original structure input must
    #   be read in and parsed
    
    #-------------------------------------------------------------------------
    # - cleanup non-empty empty lists: ie 'None', '', and None values
    #-------------------------------------------------------------------------
    addrStruct.bc.clean_address_struct(emptyContentDropSet)
    
    #-------------------------------------------------------------------------
    # - generate output files
    #-------------------------------------------------------------------------
    addrStruct.bc.write_json(os.path.join(output_path, output_file_basename))
    