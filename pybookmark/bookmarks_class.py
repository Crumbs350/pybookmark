#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bookmarks_class defines the bookmark data types as classes
these classes will be deployed in a strangle pattern to slowly
replace most bookmarks_parse.py function calls. Using the class should reduce
extra structure type & value control code in scripts, though the classes are
designed to allow direct assignment, recall by list or dict super type to not
completely break existing code

    addrStruct: dictionary of url keys with list of list values
        key = addr
        [0] = label
        [1] = age
        [2] = tags
        [3] = location
        [4] = description
        [5] = file location

@author: Crumbs
"""
import datetime
import json
import re
import sys


def List_Valid_Element(value, index):
    if isinstance(value, list):
        if len(value) == 0:
            return value
        else:
            return value[min(index, len(value)-1)]
    else:
        return value

class AgeAsInt():
    """ class for integer value that tracks time; simpler than datetime
    can not use int as super class because int is immutable so this is
    just a simple integer dummy store with support functions to alter/report
    the integer value which is a datetime, POSIX, etc time stand in
    """
    def __init__(self, value:int):
        if not isinstance(value, int):
            # force string integer to integer
            # print(f'AgeAsInt flag type: {value}') # debug
            value = int(value)
        self.value = value
        
    def __str__(self):
        return str(self.value)
    
    def __eq__(self, other):
        # need custom == test to look at values only and not memory address
        # print(f'eq test! {type(other)}') # debug
        if isinstance(other, AgeAsInt):
            # print('type match') # debug
            return self.value == other.value
        else:
            # print('type fail') # debug
            return False
        
    def __ge__(self, other):
        # need custom >= test to look at values only and not memory address
        if isinstance(other, AgeAsInt):
            return self.value >= other.value
        else:
            return False
    
    def __gt__(self, other):
        # need custom > test to look at values only and not memory address
        if isinstance(other, AgeAsInt):
            return self.value > other.value
        else:
            return False
        
    def __hash__(self):
        # hash necessary for set to work with type
        return hash(self.value)
    
    def __le__(self, other):
        # need custom <= test to look at values only and not memory address
        if isinstance(other, AgeAsInt):
            return self.value <= other.value
        else:
            return False
        
    def __len__(self):
        return 1
    
    def __lt__(self, other):
        # need custom < test to look at values only and not memory address
        if isinstance(other, AgeAsInt):
            return self.value < other.value
        else:
            return False
    
    def __ne__(self, other):
        # need custom != test to look at values only and not memory address
        return not self.__eq__(other)
    
    def __repr__(self):
        return str(self.value)
    
    def get_datetime(self):
        return datetime.datetime.fromtimestamp(self.value)
    
    def get_time_str(self):
        return str(self.get_datetime())

    def get_value(self):
        return self.value
    
    def set_by_datetime(self, datetime:datetime.datetime):
        print(f'{int(datetime.timestamp())}')
        self.value = int(datetime.timestamp())


class bookmarkAttr(list):
    """ define the basic bookmark attribute data object
    fundamentally a list of lists so inherit from list.
    
    the age value could be stored as a bare AgeAsInt() rather than a list,
        but, but for simplicity, decided to be consistent and all are lists
        could mod and exit in set_array but other places to handle as well
        see RRR: AgeAsInt assorted notes, as well as support.field_to_list()
        that means when age is used must convert to/from list value. set forces
        list, just add get_value mod to drop list.

    does NOT include the URL by default because stored at a higher level
    
    if want an empty class call with empty (), example: x = bookmarkAttr(())

    Args:
        *args: pass list of lists to define bookmark object
        **kwargs: passed named list to define bookmark object
            warning just because you define it does not mean
            the code will respect it. Use valid object labels
            note kwargs overwrites

    """

    # define the base elements map, do not define non-sequential int keys
    bookmark_map_forward = {
        0:'label',
        1:'age',
        2:'tags',
        3:'location',
        4:'description',
        5:'file location',
    }
    # add the reverse lookup
    bookmark_map_reverse = {}
    for bmk in bookmark_map_forward.keys():
        bookmark_map_reverse[bookmark_map_forward[bmk]] = bmk
    del bmk

    # use default init
    def __init__(self, *args):
        self.data = {}
        # print(f'start init yo: {type(args)}::{len(args)}')  # debug
        super().__init__(args[0])
        self._clean()  # this adds to data and forces all elements to []

    # def __str__(self):  # YYY trying to debug json export
    #     return str(list(self))
    
    # def __repr__(self): # YYY trying to debug json export
    #     return str(list(self))

    def _check_index(self, index):
        """ check to see if integer is allowed in bookmark_map_forward
        Args:
            index (int): the integer index you wish to check
        """
        if index not in self.bookmark_map_forward:
            tb = sys.exc_info()[2]
            raise IndexError(
                'index not valid for bookmark_map_forward').with_traceback(tb)

    def _clean(self, overwrite:bool=True):
        """ force all list elements to type list and adds to data dictionary 
        uses overwrite by default because called during initialization
        Args:
            overwrite (bool): if True then overwrite the existing value
        """
        for index, value in enumerate(self):
            self.set_value(index, value, overwrite=overwrite)

    def get_array(self):
        """ return full attributes that can exist as a list
        undefined attributes are returned as empty list []
        """
        data_array = []
        for index in self.bookmark_map_forward.keys():
            key = self.bookmark_map_forward[index]
            if key in self.data.keys():
                data_array.append(self.data[key])
            else:
                data_array.append([])    # RRR: AgeAsInt, default value
        return data_array

    def get_dict(self):
        """ return the defined attributes as a dictionary """
        return self.data

    def get_value(self, key, age_drop_list=True):
        """ get a specific attribute by name

        Args:
            key (str|int): 
                if string must be a defined attribute
                if int must be a defined mappable index
                    because list subclass get_value(int) is unlikely to be used
            age_drop_list (bool): if True (default) return first value of
                list for age key instead of list
        """
        if type(key) == int:
            # must map to key name
            key = self.bookmark_map_forward[key]
        if key not in self.data.keys():
            return None
        else:
            if key == 'age':    # RRR: AgeAsInt, return
                if age_drop_list and ((type(self.data[key]) is list) and (len(self.data[key]) > 0)):
                    return self.data[key][0]
                else:
                    return self.data[key]
            else:
                return self.data[key]
        
    def remove_values(self, drop_values, debug:bool=False, addr:str='parent'):
        """
        Remove values from bookmark attributes that are in drop_values list.
        Remove_values is cleans attributes by removing irrelevant values.
        
        Removal only occurs against list elements.
        
        Args:
            drop_values (list): list of elements to remove
                example: drop_values = ['', 'None', None]
            debug (boolean): if True print changes by change in sub-list length
            addr (str): the string identifying the parent object, default='parent'
        """
        for index, value in enumerate(self):
            if (value is None) or (type(value) is not list):
                continue
            L = len(value)
            value = [x for x in value if x not in drop_values]
            self.set_value(index, value, overwrite=True)
            
            if debug:
                L2 = len(value)
                if L2 < L:
                    print(f'{L}:{L2}:{index}:{addr}')

    def set_value(self, key, value, overwrite:bool=False):
        """ set the value for key|index specified
        
        forces to list, strips strings, replaces None with valid lists

        Args:
            key (str|int): 
                if string must be a defined attribute
                if int must be a defined mappable index
            value (list): the value to set the attribute to
                forced to a list
            overwrite (bool): if True then overwrite the existing value
        """

        # - figure out what is being set first, RRR: AgeAsInt, set
        if type(key) == int:
            # must check validity and map to key name 
            #   no just map and let dict error throw
            #       self._check_index(key)
            index = key
            key = self.bookmark_map_forward[index]
        else:
            index = self.bookmark_map_reverse[key]

        # - prevent None cases, simplifies test logic below 
        #   also reduce strings and force age type
        if value is None:
            value = []  # force to empty list, RRR: AgeAsInt, default value
        if type(value) == list:
            value = [x for x in value if x is not None]
            if key == 'age':
                # RRR: AgeAsInt, force type, all must be Int or errors
                value = [x if isinstance(x, AgeAsInt) else AgeAsInt(x) for x in value]
            else:
                # clean string inputs
                value = [x.strip() if type(x) is str else x for x in value]
        else:
            if key == 'age':
                # RRR: AgeAsInt, force type, must be Int or errors
                if not isinstance(value, AgeAsInt):
                    value = AgeAsInt(value)
            else:
                if type(value) is str:
                    value = value.strip()

        # print(f'{type(index)}::{index}')  # debug

        len_self = len(self)
        # print(f'len(self): {len_self}')  # debug
        if len_self <= index:
            # elements are missing
            while len(self) < index:
                self.append([]) # RRR: AgeAsInt, default value
            if type(value) != list:
                value = [value] # RRR: AgeAsInt, list
            self.data[key] = value
            self.append(value)
        else:
            # already exist so must handle merger
            if overwrite:
                replace = True
            else:                
                value_now = self.__getitem__(index)
                if value_now is None:
                    replace = True
                else:
                    if type(value_now) == list:
                        if len(value_now) == 0:
                            replace = True
                        elif value_now[0] is None:
                            replace = True
                        else:
                            replace = False
                    else:
                        # not a list, force to list
                        replace = False
                        value_now = [value_now] # RRR: AgeAsInt, list
            if replace:
                if type(value) != list:
                    value = [value]  # RRR: AgeAsInt, list
                self.__setitem__(index, value)
                self.data[key] = value
            else:
                # do not replace existing value, must merge
                #   but only merge unique new values
                # assume value_now is a list
                if type(value) == list:
                    for vnow in value:
                        if vnow not in value_now:
                            value_now.append(vnow)
                else:
                    if value not in value_now:
                        value_now.append(value)
                self.__setitem__(index, value_now)
                self.data[key] = value_now

    def set_array_keys(self, **kwargs):
        for key, value in kwargs.items():
            # print(f'{key}::{value}') # debug
            self.set_value(key, value)
            
    def unique(self, sort:bool=True):
        """ change all values so lists are only the unique elements
        
        remove_values should be run first, if None is encountered as an element
        of a list unique will throw a TypeError that can not be recovered from
        
        Args:
            sort (bool): if True (default) sort the updated set of values
        """
        for index, value in enumerate(self):
            if value is not None:
                value_now = list(set(value))
                if sort:
                    try:
                        value_now.sort()
                    except TypeError:
                        # occurs for mixed type, sort by string values
                        sorted(value_now, key=lambda x: str(x))
                self.set_value(index, value_now, overwrite=True)
       
    def bookmark_list_to_dict(self, bookmark_list:list):
        """ given a list of values use self.bookmark_map_forward to convert the
        list to a dictionary to use with set_array_keys to define object values
        Args:
            bookmark_list (list)
        
        """
        bookmark_dict = {}
        for key_index in self.bookmark_map_forward:
            bookmark_dict[self.bookmark_map_forward[key_index]] = bookmark_list[key_index]
        return bookmark_dict
        
    def serialize(self):
        """ convert all types and sub-types to serializable base types
        how: copy list to avoid modifying self data definition,
            then map AgeAsInt to a serializable type
        """
        list_use = self.get_array()
        age_index = self.bookmark_map_reverse['age'] # 1
        if isinstance(list_use[age_index], list):
            # this is expected
            list_use[age_index] = [str(x) for x in list_use[age_index]]
            if len(list_use[age_index]) == 1:
                # de-list the age to match original save and reduce JSON file size
                list_use[age_index] = list_use[age_index][0]
        else:
            # this is to be complete
            list_use[age_index] = str(list_use[age_index])
        return list_use
    
    def to_json(self):
        """ return a JSON string version of the class
        ref: https://pynative.com/make-python-class-json-serializable/
        """
        return json.dumps(self.serialize())


class bookmarks(dict):
    """ define bookmarks dictionary.
    key = url
    value = a bookmarkAttr object
    
    To add or change single bookmarks use add, delete and replace
    To define bookmarks
        from a list of lists use build_address_struct
        from a file, use read_json
    To tidy bookmarks use clean_address_struct and unique
    To search bookmarks use search_address_struct*
    To save bookmarks use write_json
    """

    def __init__(self, *args):
        super().__init__()
        if len(args) > 0:
            if type(args[0]) is dict:
                # a dictionary was passed
                self._build_address_struct_by_dict(args[0])
            else:
                raise(f'Invalid user input, {type(args[0])}, ' +
                      'Expected dictionary of lists of lists.')
        
    # def __repr__(self): # YYY trying to debug json export
    #     rep_str = "__repr__{"
    #     for url in self.keys():
    #         print(f'{type(self[url])}')
    #         rep_str += f"'{url}':{self[url]}\n"
    #     rep_str = rep_str[:-2] + "}"
    #     return rep_str
    
    # def __str__(self): # YYY trying to debug json export
    #     rep_str = "__str__{"
    #     for url in self.keys():
    #         rep_str += f"'{url}':{self[url]}\n"
    #     rep_str = rep_str[:-1] + "}"
    #     return rep_str
    
    def _build_address_struct_by_dict(self, dict_in:dict):
        """ user passed dict, convert to use bookmarks class and bookmark class
        sub-objects 
        Args:
            dict_in (dict): dictionary, key = url and value = list of lists
        Returns:
            None, dict_in loaded by add into object
        """
        for url_key in dict_in:
            value = dict_in[url_key]
            # print(f'basbd: {url_key}:::{value}') # debug
            if type(value) is not list:
                print(f'Invalid user input:\n\t{url_key}::{value}.\n' +
                      'Expected dictionary of lists of lists.')
                continue
            else:
                # list of lists to parse into bookmark_attr object
                bookmark_attributes = bookmarkAttr(())
                use_dict = bookmark_attributes.bookmark_list_to_dict(value)
                bookmark_attributes.set_array_keys(**use_dict)
                self.add(url_key, bookmark_attributes)
        
    def add(self, url:str, bookmark:bookmarkAttr):
        if url in self:
            tb = sys.exc_info()[2]
            raise KeyError(
                'dictionary can not add to existing key use replace').with_traceback(tb)
        self[url] = bookmark
    
    def delete(self, url:str):
        del self[url]
        
    def replace(self, url:str, bookmark:bookmarkAttr):
        self[url] = bookmark
            
    def build_address_struct(self, addresses:list):
        """
        build (and extend) dictionary by address and list data structure
        merges but does not clean the data generated by parse_html
        
        Args:
            addresses (list): output of parse_path(), list of lists, each sub-
                list is an individual bookmark from the files parsed defined as:
                [0] label
                [1] url
                [2] age
                [3,4,5] must define due to being output of prior process but not used
                [6] tag
                [7] location    
                [8] description, not always defined
                [8,9] file location
                
                note: unlike higher level structure the sub-list elements can
                    not be lists ie
                    [a, b, c] where a = list, b = list, c = list but elements
                    of a, b, and c are not list
        Returns:
            modifies core class dictionary definition
        """
        match_char = re.compile(r'\w')  # match characters a-z0-9 space etc
        for addrlist in addresses:
            # increase read ability by defining variables for information to assign
            addr_lab = addrlist[0]
            addr_url = addrlist[1]
            addr_age = addrlist[2]
            addr_tag = addrlist[6]
            addr_loc = addrlist[7].strip()
            
            # decide how to handle description (if defined) and file location
            addrlist_len = len(addrlist)
            if addrlist_len == 9:
                addr_dsc = None     # description is not defined in this case
                addr_fil = addrlist[8]
            elif addrlist_len == 10:
                addr_dsc = addrlist[8]
                addr_fil = addrlist[9]
            else:
                addr_dsc = None    # avoid use below
                addr_fil = None    # avoids use below
                print(f'Warning: build_address_struct: Unclear how to handle length {addrlist_len} for {addrlist}')
            
            if addr_url in self.keys():
                # append to the existing address in the address structure
                # note this only checks the first element being the same
                #   should technically do "in" for list but instead call
                #   unique() later so redesigned code behavior matches existing
                
                # addrStruct[addr_url][0]   # label append not the same
                if self[addr_url].get_value('label')[0] != addr_lab:
                    self[addr_url].set_value('label', addr_lab)
             
                # addrStruct[addr_url][1]   # age keep oldest
                if addr_age is not None:
                    if (self[addr_url].get_value('age') is None) or \
                        (self[addr_url].get_value('age')[0] > addr_age):
                        self[addr_url].set_value('age', addr_age, overwrite=True)
                
                # addrStruct[addr_url][2]   # tags append not the same
                if addr_tag is not None:
                    if len(self[addr_url].get_value('tags'))==0:
                        self[addr_url].set_value('tags', addr_tag)
                    elif self[addr_url].get_value('tags')[0] is None:  # replace None
                        self[addr_url].set_value('tags', addr_tag, overwrite=True)
                    else:  # append unique values to not None
                        if self[addr_url].get_value('tags')[0] != addr_tag:
                            self[addr_url].set_value('tags', addr_tag)
                
                # addrStruct[addr_url][3]   # location append not the same
                if addr_loc is not None:
                    if len(self[addr_url].get_value('location'))==0:
                        self[addr_url].set_value('location', addr_loc)
                    elif self[addr_url].get_value('location')[0] is None:  # replace None
                        self[addr_url].set_value('location', addr_loc, overwrite=True)
                    else:  # append unique values to not None
                        if self[addr_url].get_value('location')[0] != addr_loc:
                            self[addr_url].set_value('location', addr_loc)
                
                if (addr_dsc is not None and
                    match_char.search(addr_dsc) is None):
                    # remove non-word descriptions like \n
                    addr_dsc = None
                
                # addrStruct[addr_url][4]   # description append not the same
                if addr_dsc is not None:
                    if len(self[addr_url].get_value('description'))==0:
                        self[addr_url].set_value('description', addr_dsc)
                    elif self[addr_url].get_value('description')[0] is None:  # replace None
                        self[addr_url].set_value('description', addr_dsc, overwrite=True)
                    else:  # append unique values to not None
                        if self[addr_url].get_value('description')[0] != addr_dsc:
                            self[addr_url].set_value('description', addr_dsc)
    
                # addrStruct[addr_url][5]   # file location append not the same
                if addr_fil is not None:
                    if len(self[addr_url].get_value('file location'))==0:
                        self[addr_url].set_value('file location', addr_fil)
                    elif self[addr_url].get_value('file location')[0] is None:  # replace None
                        self[addr_url].set_value('file location', addr_fil, overwrite=True)
                    else:  # append unique values to not None
                        if self[addr_url].get_value('file location')[0] != addr_fil:
                            self[addr_url].set_value('file location', addr_fil)                
            else:
                # create address in the address structure
                new_bookmark = bookmarkAttr(())
                new_bookmark.set_array_keys(
                    **{'label': [addr_lab],
                     'age': addr_age,
                     'tags': [addr_tag],
                     'location': [addr_loc],
                     'description': [addr_dsc],
                     'file location': [addr_fil]
                     }
                    )
                self.add(addr_url, new_bookmark)
        
    def clean_address_struct(self, emptyContentDropSet:list, debug:bool=False):
        """
        Clean up bookmark sub-elements by removing irrelevant values. Removes
        emptyContentDropSet items from each element sub-list.
        
        Removal only occurs against list elements.
        
        Args:
            emptyContentDropSet (list): list of elements to remove
                example: emptyContentDropSet = ['', 'None', None]
            debug (boolean): if True print changes by change in sub-list length
        Returns:
            modifies core class dictionary definition
        """
        for addr in self.keys():
            self[addr].remove_values(emptyContentDropSet, debug, addr)
        
    def read_json(self, filename):
        """
        read addrStruct from json formated file at location filename
        function assumes file exists and will error if not.
        
        warning this appends any existing dictionary definition by add. it will
            fail if duplicates exist
        
        Args:
            filename (str): string path to read from
        Returns:
            None or dictionary addrStruct
            addrStruct (dict): dictionary of url keys with list of list values
                created by buildAddressStruct
        """
        with open(filename, 'r') as fJson:
            json_dict = json.load(fJson)
            self._build_address_struct_by_dict(json_dict)
        
    def search_address_struct(self, pattern, element, ignore_case=False, url_list=None):
        """
        search for pattern in element
        
        Args:
            pattern (str): string pattern to pass to re to use for search
                if element == 1 then treats ># or <# as: age > #   or   age < #
            element (int|str): integer element to search, matches attribute mapping
                for the bookmarkAttr class. mapped to int if attribute string passed 
                 [-1] = search addresses themselves
                 [0] = label
                 [1] = age
                 [2] = tags
                 [3] = location
                 [4] = description
                 [5] = file location
            ignore_case (bool): if True pass re.IGNORECASE to regex
                default = False
            url_list (list): list of urls to use, ie a subset of the defined
                address structure. if None (default) then uses self.keys()
        Returns:
            list: urls where pattern was found in element
        """
        # checking element against bookmarkAttr forces early failure for bad input
        y = bookmarkAttr(()) # temporary value only used for reverse lookup
        if type(element) is str:
            # convert element to numeric index
            element_str = element
            element = y.bookmark_map_reverse[element]
        else:
            # assumes int
            if element != -1:
                element_str = y.bookmark_map_forward[element]
        
        if url_list is None:
            url_list = self.keys()
        
        found_list = []
        if element == 1:
            # checks age
            if pattern[0] == '>':
                pattern = pattern[1:].strip()
                for addr in url_list:
                    if self[addr].get_value('age')[0] > pattern:
                        found_list.append(addr)
            elif pattern[0] == '<':
                pattern = pattern[1:].strip()
                for addr in url_list:
                    if self[addr].get_value('age')[0] < pattern:
                        found_list.append(addr)
        else:
            if ignore_case:
                repc = re.compile(pattern, flags=re.IGNORECASE)
            else:
                repc = re.compile(pattern)
            
            if element == -1:
                for addr in url_list:
                    # all values are lists because handle above non-list age
                    if repc.search(addr) is not None:
                        found_list.append(addr)
            else:
                # searches for pattern string match in list of values
                for addr in url_list:
                    # all values are lists because handle above non-list age
                    val = self[addr].get_value(element)
                    for vali in val:
                        if vali is None:  # most likely to occur for 2=tags
                            continue
                        if repc.search(vali) is not None:
                            found_list.append(addr)
        return found_list

    
    def search_address_struct_print(self, urls, element):
        """print the address + requested element
        
        Args:
            urls (list): output of search_address_struct or search_address_struct_wrapper
            element (int|str): integer element to search, matches attribute mapping
                for the bookmarkAttr class. mapped to int if attribute string passed
        Returns:
            None just prints to stdout
        
        """
        
        if type(element) is str:
            # convert element to numeric index
            element_str = element
            y = bookmarkAttr(())
            element = y.bookmark_map_reverse[element]
        else:
            # assumes int
            if element != -1:
                element_str = y.bookmark_map_forward[element]
        
        if type(urls) is str:
            urls = [urls]
        
        print(f'Printing element {element} named {element_str} for urls passed')
        for addr in urls:
            if addr in self.keys():
                print(f'{addr}::{self[addr].get_value(element)}')
    
    
    def search_address_struct_wrapper(self, pattern, element, ignore_case=False):
        """
        calls search_address_struct to search for pattern in element
        where element can be a list or pattern can be a dictionary of patterns
        vs int. works by calling search_address_struct and returning the set
        of the matched addresses as a list
        
        Args:
            pattern (str|dict|list): 
                if string then same as searchAddressStruct() pattern to search
                    applied to all element specified by list
                if list then either searches single element or 1:1 mapping
                    is applied to create pattern element pairs
                if dict then key=element, value = pattern
            element (int|list): integer element to search, or -1 for address
                ignored if pattern is dict
                if int: then only searches 1 element
                if list: then searches many elements for pattern(s)
                see searchAddressStruct for definition of int values
            ignore_case (bool): if True pass re.IGNORECASE to regex
                default = False
        Returns:
            list: urls where pattern(s) was found in element(s) searched
        """
        # QQQ use search url_list to reduce/fix issues with search in GUI?
        found_list = []
        if type(pattern) is dict:
            for element in pattern.keys():
                pattern_search = pattern[element]
                found_list = found_list + \
                    self.search_address_struct(pattern_search, element, ignore_case)
        elif type(pattern) is list:
            if type(element) is list:
                # pattern list, element list; must be the same length
                if len(pattern) != len(element):
                    return None
                for n in range(0, len(pattern)):
                    found_list = found_list + \
                        self.search_address_struct(pattern[n], element[n], ignore_case)
            elif type(element) is int:
                # pattern list, element int
                for n in range(0, len(pattern)):
                    found_list = found_list + \
                        self.search_address_struct(pattern[n], element, ignore_case)
        else:
            # string pattern and list or int element
            if type(element) is list:
                # pattern str, element list
                for elementi in element:
                    found_list = found_list + \
                        self.search_address_struct(pattern, elementi, ignore_case)
            elif type(element) is int:
                # pattern str, element str; this case is like non-wrapper
                found_list = self.search_address_struct(pattern, element, ignore_case)
        
        return list(set(found_list))

    def serialize(self):
        """ serialize values to allow json to work 
        this converts AgeAsInt to a JSON serializable type
        """
        # copy dict, avoid modifying self data definition, then map AgeAsInt
        #   to a serializable type. copy of self.__dict__.copy() failed
        # so just build it against self which works
        
        dict_use = {}  # self.__dict__.copy()
        # print('Running bookmarks serialize')
        # print(f'{len(dict_use)}::{len(self.__dict__)}::{len(self)}::{len(list(self.keys()))}') # 0::0::X::X
        for url_key in self:
            value = self[url_key]
            # know each value is a bookmarkAttr so no isinstance check or list verify
            dict_use[url_key] = value.serialize()
        # print(f'{len(dict_use)}::{len(self)}')
        return dict_use
        
    def unique(self, sort=True):
       """ reduce all attributes to only the unique elements
       Args:
           sort (bool): if True (default) sort the updated set of values
       """
       for url in self.keys():
           self[url].unique()

    def write_json(self, filename, indent=None):
        """
        write bookmark address structure to filename as a json formatted file
        function assumes path directory structure exists and will error if not
        
        the addrStruct is a list of url keys with list of list values
        
        Args:
            filename (str): string path to write to
            indent (int): if not None (default), prints pretty json output using
                value as the number of spaces to indent children. pretty is not a
                default because makes output files bigger. suggested indent=2
        Returns:
            None.
        """
        with open(filename, 'w') as fJson:
            json.dump(self.serialize(), fJson, indent=indent)

    
    #
    # - non-class Address_Struct, ie bookmarks class, related functions
    #

    @staticmethod
    def Address_List_Converter(url:str, bookmark:bookmarkAttr):
        """
        convert url + bookmarkAttr to addresses style list data structure
        this mostly exists only for testing arbitrary inputs to 
        build_address_struct()
        
        Args:
            url (str): url for the bookmark
            bookmark (bookmarkAttr): attributes of the bookmark
                caveat: because only single values are expected in how
                    the output is used, function drops list to first element
        Returns:
            address (list): output a single addressparse_path(), list of lists, each sub-
                list is an individual bookmark from the files parsed defined as:
                [0] label
                [1] url
                [2] age
                [3,4,5] must define due to being output of prior process but not used
                [6] tag
                [7] location
                [8] description, not always defined
                [8,9] file location
        """
        return [List_Valid_Element(bookmark.get_value('label'), 0),
                url,
                List_Valid_Element(bookmark.get_value('age'), 0),
                [], [], [],
                List_Valid_Element(bookmark.get_value('tags'), 0),
                List_Valid_Element(bookmark.get_value('location'), 0),
                List_Valid_Element(bookmark.get_value('description'), 0),
                List_Valid_Element(bookmark.get_value('file location'), 0)
                ]
    
    @staticmethod
    def Address_Struct_Compare(addrStruct1, addrStruct2, verbose = False):
        """
        Given 2 addrStruct compare them by address. When duplication occurs provide
        context
        
        Args:
            addrStruct1 (dict): dictionary of url keys with list of list values
                of the type generated by readAddressStruct or buildAddressStruct
                works if dict or if bookmarks class
            addrStruct2 (dict): dictionary of url keys with list of list values
                of the type generated by readAddressStruct or buildAddressStruct
                works if dict or if bookmarks class
        Returns:
            addresses (tuple): (list of urls with different data, 
                                list of url keys only in 1,
                                list of url keys only in 2)
        """
    
        addresses1 = set(list(addrStruct1.keys()))
        addresses2 = set(list(addrStruct2.keys()))
        addr1only = list(addresses1.difference(addresses2))
        if verbose:
            for addr in addr1only:
                print(f'a1 only: {addr}')
        addr2only = list(addresses2.difference(addresses1))
        if verbose:
            for addr in list(addresses2.difference(addresses1)):
                print(f'a2 only: {addr}')
        addrdelta = []
        for addr in list(addresses1.intersection(addresses2)):
            a1 = addrStruct1[addr]
            a2 = addrStruct2[addr]
            if a1 != a2:
                addrdelta.append(addr)
                if verbose:
                    print(f'a1 != a2: {addr}')
                    print(f'\t{a1}')
                    print(f'\t{a2}')
            
        return (addrdelta, addr1only, addr2only)
    
    @staticmethod
    def Address_Struct_Merge(addrStruct1, addrStruct2, merge_rule, dict_out=False):
        """
        Given 2 bookmarks objects merge them by address. 
        When duplication occurs follow the merge rules defined by merge_rule
        
        Args:
            
            addrStruct1 (bookmarks): dictionary of url keys with list of list values
                of the type generated by readAddressStruct or buildAddressStruct
            addrStruct2 (bookmarks): dictionary of url keys with list of list values
                of the type generated by readAddressStruct or buildAddressStruct
            merge_rule (int): definition determines how duplicate urls are merged
                0: the content is merged when lists are allowed, else use 1    
                1: addrStruct1 content is used
                2: addrStruct2 content is used
            dict_out (bool): if True returns dict, if False (default) returns a
                bookmarks class object
        Returns:
            addrStruct (bookmarks): dictionary of url keys with list of list values
                defined as bookmarks class object whose super class is dict
        """
    
        addresses1 = list(addrStruct1.keys())
        addresses2 = list(addrStruct2.keys())
        addrStructNew = {}
        for addr in list((set(addresses1)).union(set(addresses2))):
            a1 = addr in addrStruct1
            a2 = addr in addrStruct2
            if a1 and (merge_rule==1 or not a2):  # using 1 or only 1
                addrStructNew[addr] = addrStruct1[addr].copy()
            elif a2 and (merge_rule==2 or not a1): # using 2 or only 2
                addrStructNew[addr] = addrStruct2[addr].copy()
            else:
                # in both and set merge
                addr_element = []
                for index in range(max(len(addrStruct1[addr]), len(addrStruct2[addr]))):
                    if ((addrStruct1[addr][index] == addrStruct2[addr][index]) or
                        type(addrStruct1[addr][index]) is not list):
                        addr_element.append(addrStruct1[addr][index])
                    else:
                        # they are not equal and the type is list
                        listnew = []
                        L1 = len(addrStruct1[addr][index])
                        L2 = len(addrStruct2[addr][index])
                        for index2 in range(max(L1, L2)):
                            if index2 >= L1:
                                # use 2
                                if addrStruct2[addr][index][index2] not in listnew:
                                    listnew.append(addrStruct2[addr][index][index2])
                            elif index2 >= L2:
                                # use 1
                                if addrStruct1[addr][index][index2] not in listnew:
                                    listnew.append(addrStruct1[addr][index][index2])
                            else:
                                # check append both
                                if addrStruct1[addr][index][index2] not in listnew:
                                    listnew.append(addrStruct1[addr][index][index2])
                                if addrStruct2[addr][index][index2] not in listnew:
                                    listnew.append(addrStruct2[addr][index][index2])
                        addr_element.append(listnew)
                addrStructNew[addr] = addr_element
        if dict_out:
            return addrStructNew
        else:
            return bookmarks(addrStructNew)
       
    @staticmethod 
    def Address_Struct_Read(filename):
        """
        read addrStruct from json formated file at location filename
        function assumes file exists and will error if not.
        
        Args:
            filename (str): string path to read from
        Returns:
            None or bookmarks class dictionary addrStruct object
        """
        addrStruct = None
        with open(filename, 'r') as fJson:
            addrStruct = bookmarks(json.load(fJson))
        return addrStruct
