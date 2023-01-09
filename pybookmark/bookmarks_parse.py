#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parse bookmarks.html, get folder information and add to each link
Creates structured output.

bookmarks.html format:
    dl marks folders
    dd marks descriptive elements added to links

 Only functions parse_path(), parse_html() and buildAddressStruct() are really
 intended to be exported though others like file_age and string* could be.
 The tagElement and getChildren soup functions are meant to be internal only.
 Add to export list *AddressStruct() set of utilities for read, write, search
     

Usage: python3 bookmarks_parse.py > bookmarks_parse_file_test.txt
    output can be imported as comma separated quoted string to spreadsheet

Operation Pseudo Code:
    uses beautiful soup
    the soup number of contents is the number of tags present in that place
    call to break up or ID tags at each level? yes
    for each type Tag just keep calling loop to break up.
    pass the current level and folder list
    pop the folder list when move out of folder


    add folder
    loop next list
    drop folder

note: tags.attrs gives the list of possible tags
 
fast debug folder structure extraction method:
    modify hardcoded bookmarks file in main
    call from command line:
        $ python bookmarks_parse.py &> debug_output.txt
    grep output for Exit Folder
        $ grep 'Exit folder' debug_output.txt

TODO: 
    Code code be rewritten to use class for addrStruct.

@author: Crumbs
"""
#import BeautifulSoup as bs    # beautifulSoup version 3
import bs4 as bs    # beautifulSoup 4
import glob
import os
import re
import sys


def file_age(file_abs_path):
    """
    Return file modification time for the passed file
    """
    return(os.stat(file_abs_path)[8])


# buildAddressStruct moved to bookmarks_class as build_address_struct

# cleanAddressStruct moved to bookmarks_class as clean_address_struct

# mergeAddressStruct moved to bookmarks class file as Address_Struct_Merge

# readreadAddressStruct moved to bookmarks class as read_json and Address_Struct_Read
        
# searchAddressStruct moved to bookmarks class as search_address_struct
# searchAddressStructPrint moved to bookmarks class as search_address_struct_print
# searchAddressStructWrapper moved to bookmarks class as search_address_struct_wrapper
    
# writeAddressStruct moved to bookmarks class as write_json

# file_read_file_location_mod, file_read_label_mod_by_addr moved to support


def tagElement(ELEM, FOLDER_LIST, DEBUG):
    """
    given an ELEM and FOLDER_LIST soup element return updated FOLDER_LIST
    and ELEMENT information to append at a higher level to list of ELEMENTS

    Args:
        ELEM        current tag
        FOLDER_LIST list of folders, last is lowest, first is highest level
        DEBUG       boolean, if true print messages
    Returns:
        3 Lists
        1: NONE or single element information for address or dd
            must append dd to the last address
        2: FOLDER_LIST
        3: ELEM_TYPE
            None = None
            0 = dd = descriptor
            1 = ahref = link
            2 = folder
            3 = folder name (h3)
            4 = folder name parent (h1) = bookmarks menu
    """

    if (DEBUG):
        print('Type == ' + str(type(ELEM)) + '::' + stringNChar(str(ELEM), 50))

    if ELEM.name is None:
        return(None, FOLDER_LIST, None)

    # -- build all the regular expression matches
    sa = re.compile('^a')
    s1 = re.compile('^h1')
    s3 = re.compile('^h3')
    sd = re.compile('^dd')
    sl = re.compile('^dl')
    #rb = re.compile('Recently Bookmarked')
    #rt = re.compile('Recently Tags')

    # -- put most common matches at top to reduce if checks
    # put folder entry before exit to handle case when new folder starts
    #   inside the current right as the current ends.
    #

    if len(ELEM.contents) == 0:
        # handle empty name case; example http link but no string descriptor
        if (DEBUG):
            print('Got empty: ' + str(type(ELEM)) + stringNChar(str(ELEM), 50))
        ELEM.contents.append("")

    # - ahref
    if (re.search(sa, ELEM.name) is not None \
        and (
        ELEM.contents[0] != 'Recently Bookmarked' and \
        ELEM.contents[0] != 'Recent Tags'
                )):
        # throw out if Recent Tags or recently bookmarked is found
        # contents is the name

        # change to address structure; tags? other elements to store?
        #TAGS:add_date
        #TAGS:href
        #TAGS:icon              drop
        #TAGS:icon_uri          drop
        #TAGS:last_charset
        #TAGS:last_modified
        #TAGS:shortcuturl
        #TAGS:tags
        #TAGS:unfiled_bookmarks_folder      assigned to OTHER_BOOKMARKS folder
        #TAGS:web_panel         drop
        addrList = [ELEM.contents[0], \
                    ELEM.get('href'), \
                    ELEM.get('add_date'), \
                    ELEM.get('last_modified'), \
                    ELEM.get('last_charset'), \
                    ELEM.get('shortcuturl'), \
                    ELEM.get('tags'), \
                    '::'.join(FOLDER_LIST)
                    ]

        if (DEBUG):
            print('::'.join(FOLDER_LIST) + "--" + ELEM.contents[0])

        return(addrList, FOLDER_LIST, 1)

    # - dd descriptors
    if (re.search(sd, ELEM.name) is not None):
        return(ELEM.contents[0], FOLDER_LIST, 0)

    # - folder names (h3)
    if (re.search(s3, ELEM.name) is not None):
        # h3 match for folder names, just append name to the folder list
        FOLDER_LIST.append(ELEM.contents[0])
        return(None, FOLDER_LIST, 3)

    # - folder names (h1)
    if (re.search(s1, ELEM.name) is not None):
        # h1 match for folder names, just append name to the folder list
        FOLDER_LIST.append(ELEM.contents[0])
        return(None, FOLDER_LIST, 4)

    # - enter new folder (note code never reached previously because of length > 1 requirement (removed)
    if (re.search(sl, ELEM.name) is not None):
        # enter the sub-folder to parse elements
        # tracked by using length of structure at higher level
        # add the current folder to the folder list is this needed?
        #folderLevelList.append(currentFolderList)
        if (DEBUG):
            print('Enter new folder element' + ':'.join(FOLDER_LIST))
        return(None, FOLDER_LIST, 2)

    # - got to the end return nothing
    return(None, FOLDER_LIST, None)


def getChildren(SOUP, ADDRESS_SET, FOLDER_LIST, FOLDER_PTR, DEBUG, LEVEL=0):
    """
    Loop interative call to move into soup

    Args:
        SOUP            ie bs.BeautifulSoup( doc ) or a sub-portion there-of
        ADDRESS_SET     list of address information
        FOLDER_LIST     list of folders
        FOLDER_PTR      integer pointer into FOLDER_LIST
        DEBUG           boolean, if true print messages
        LEVEL           integer counter that tracks recursive getChildren call
                        only prints when DEBUG = True
    Returns:
        address set
        FOLDER_LIST
        FOLDER_PTR
        
    dev note: using SOUP.get_text() vs str(SOUP) solves some recursion issues
        except get_text() does not include html formatting, which breaks code
        that tries to match the formatting; therefore use SOUP.name for that
        note: 
            str(SOUP) returns UTF-8
            SOUP.decode() also returns str but in unicode, 
            SOUP.decode_contents() returns str but without leading element
            SOUP.get_text() is only the human readable text
        per ref: https://stackoverflow.com/questions/31528600/beautifulsoup-runtimeerror-maximum-recursion-depth-exceeded
    """

    if DEBUG:
        print(f'getChildren call level = {LEVEL}')
    LEVEL = LEVEL + 1
    
    # - first handle if new folder or not
    soup_text = (SOUP.decode()).replace('\r', ' ').replace('\n', ' ')
    #   was using SOUP.get_text() but it doesn't include html formatting
    #   need html formatting for the next line to work
    #   SOUP.name gives the current element so don't have to use a string
    if SOUP.name == 'dl':
        #if (re.search('^<dl>', stringNChar(soup_text, 10)) is not None):
        newFolder = True
        if (DEBUG):
            print('SOUPI' + str(len(SOUP)) + ':enter:' +
              stringNChar(soup_text, 100))
    else:
        newFolder = False
        if (DEBUG):
            print('SOUPI' + str(len(SOUP)) + '::' +
              stringNChar(soup_text, 100))

    # - now handle the sub elements of the passed SOUP
    tagNowI = -1
    while (tagNowI < (len(SOUP)-1)):
        tagNowI = tagNowI + 1

        # only process Tags
        if (re.search('Tag', str(type(SOUP.contents[tagNowI]))) is None):
            continue

        soupLength = len(SOUP.contents[tagNowI])
        if (DEBUG):
            print('getChildren: ' + str(tagNowI) + '::' + str(soupLength))

        if (soupLength == 0):
            continue

        if (soupLength == 1):
            if (DEBUG):
                if type(SOUP.contents[tagNowI]) is bs.element.NavigableString:
                    print('found:: ' + (SOUP.contents[tagNowI].title()))     
                else:
                    print('found:: ' + (SOUP.contents[tagNowI].get_text()))

            (addr, FOLDER_LIST, elemType) = tagElement(
                    SOUP.contents[tagNowI], FOLDER_LIST, DEBUG)
            if (DEBUG):
                print('element type: ' + str(elemType))

            if (elemType == 0 and addr is not None):
                # append the dd information string to the last address
                ADDRESS_SET[len(ADDRESS_SET)-1].append(addr)
            elif (elemType == 1 and addr is not None):
                # append the latest address information to the ADDRESS_SET
                ADDRESS_SET.append(addr)
            elif (elemType == 2):
                # 2: increment the folder pointer; QQQ okay but how to leave folder?
                if (tagNowI < len(SOUP)-2):
                    x=1
                    if (len(SOUP.contents[tagNowI+1]) == 1):
                        # empty folder must leave (fixes Raspberry pi issue but not Entertainment and Lifestyle not-leaving folder issue)
                        x = FOLDER_LIST.pop()
                        if (DEBUG):
                            print('Drop Bad folder:' + x)
            elif (elemType == 3 or elemType == 4):
                # 3: folder name new; QQQ: already appended at a lower level
                # 4: folder name new; QQQ: already appended at a lower level; parent folder
                # this doesn't do anything anymore except prevent no match message
                # script not optimized so don't remove; leave for documentation
                x = 1
            else:
                # nothing happened; why?
                #   <p> gets here; needs to be folder type or is it dl that marks folders? technically both
                #   title gets here also
                #   \n gets here
                if (DEBUG):
                    print('no match by type:: ' + (SOUP.contents[tagNowI].get_text()))

        else:
            # pseudo-code if len > 1 then need to call getChildren
            # when exit after a call to getChildren then reduce FOLDER_PTR???
            #   problem decrementing FOLDER_PTR here is too overzealous
            if (re.search('empty_folder_auto_can_bus',
                          stringNChar(SOUP.contents[tagNowI].get_text(), 100)) is not None):
                x = 1
            if (DEBUG):
                print('Calling getChildren:' + str(tagNowI) + ': ' 
                      + stringNChar(SOUP.contents[tagNowI].get_text(), 100))
            (ADDRESS_SET, FOLDER_LIST, FOLDER_PTR) = getChildren(
                    SOUP.contents[tagNowI],
                    ADDRESS_SET,
                    FOLDER_LIST,
                    FOLDER_PTR, DEBUG, LEVEL)

    if newFolder:
        pre_folder = FOLDER_LIST
        FOLDER_LIST.pop()
        if (DEBUG):
            print('Exit folder (' + str(FOLDER_PTR) + ') from' + 
                  ':'.join(pre_folder) + '\n\tnow' + ':'.join(FOLDER_LIST))
        FOLDER_PTR = 0  # should it -1 instead if odd/even

    return(ADDRESS_SET, FOLDER_LIST, FOLDER_PTR)
    

def parsed_address_len(ADDR_SET):
    """
    return number of attributes by address element in the address set.

    Args:
        ADDR_SET (tuple): the data generated by parse_html()
    Returns:
        (int) length of longest address element
    """
    addrLenMax = 0
    for addrN in range(0,len(ADDR_SET)):
        addr = ADDR_SET[addrN]
        x = len(addr)
        if (x > addrLenMax):
            addrLenMax = x
    return(addrLenMax)


def parse_html(FILENAME, DEBUG=False, ADD_EMPTY=True):
    """
    Given an absolute filename to a bookmarks.html file return the address set.
    Parses addresses for folder structure. Also grabs keywords.
    
    Note used because beautiful soup was skipping links and folder names
    when did not do preprocessing.
    
    Args:
        FILENAME: path to the html file to parse
        DEBUG (bool): default=False, passed to getChildren()
    Returns:
        (tuple) = (list of addresses, soup)
        the soup is output of bs.BeautifulSoup, returned for debugging purposes
    """
    
    # read the file and pre-processing to account for abberant formating
    fileHan = open(FILENAME)
    fileString = fileHan.read()
    fileHan.close()

    # drop ICON information reduces what is parsed by beautiful soup
    fileString = re.sub(
         '(ICON_URI=").+?"', # non-greedy so only matches to next "
         '',
         fileString, flags=re.IGNORECASE
         )
    fileString = re.sub(
         '(ICON=").+?"', #
         '',
         fileString, flags=re.IGNORECASE
         )
    
    # drop emojis
    # found warning symbol UTF-8 octal bytes: 342 232 240 357 270 217    
    # ref: https://www.iemoji.com/view/emoji/163/symbols/warning
    if 0:
        # this works
        fileString = re.sub(u"\u26A0\uFE0F", '', fileString)
    else:
        # remove emojis then drop duplicate space they introduce
        fileString = string_remove_emoji(fileString)
        fileString = re.sub("  ", " ", fileString)  # replace duplicate spaces

    if ADD_EMPTY:    
        # pre-process: populate empty folders with empty html tags that can be dropped later
        fileString = re.sub(
               '<DL><p>\\n {1,}</DL><p>',
               '<DL><p>\\n           <DT><A HREF="empty">empty</A></DL><p>',
               fileString, flags=re.IGNORECASE
               )
        # pre-process: populate empty link names
        fileString = re.sub(
               '></A>',
               '>empty_string</A>',
               fileString, flags=re.IGNORECASE
               )
    
    # run pre-process string through BeautifulSoup parser
    # non-preprocessed call: soup = bs.BeautifulSoup(open(FILENAME), "lxml")
    soup = bs.BeautifulSoup(fileString, "lxml")
        
    # process the BeautifulSoup output to extract the useful info: address set
    folderNameList = list()
    addressSet = list()
    (addressSet, folderNameList, folderPointer) = \
        getChildren(soup, addressSet, folderNameList, -1, DEBUG)
    
    return(addressSet, soup)


def parsed_max_address_len(ADDR_SET):
    """
    return maximum number of attributes by address element in the address set.
    
    Args:
        ADDR_SET (tuple): the data generated by parse_html()
    Returns:
        (int) length of longest address element
    """
    addrLenMax = 0
    for addrN in range(0,len(ADDR_SET)):
        addr = ADDR_SET[addrN]
        x = len(addr)
        if (x > addrLenMax):
            addrLenMax = x
    return(addrLenMax)
    

def parse_path(file_path, ncpu=1):
    """
    For *bookmark*.html files within file_path tree, use parse_html to parse
    for links. List of files generated by recursive search.
    
    Args:
        file_path (str): system file path to look for html files to parse
            if file_path is a list treats as individual set of files to 
            process not a path to search
        ncpu (int): number of processes, 1 or >1. if > 1 then multiprocessing
            XXX but not currently implemented because numerous overlapping
            lists defined and decided not worth the effort.
    Returns: (addresses, file_ages, bad_files)
        addresses = list of lists, contains bookmarks in files parsed 
        file_ages = dictionary of files parsed.
            key = file, value = modification time
        bad_files = list of files that fail to process
        
        will return (None, None, None) if invalid input
    """
    if type(file_path) is str:
        files = glob.glob(os.path.join(file_path, '**/*.html'), recursive=True)
    elif type(file_path) is list:
        files = file_path
    else:
        print(f'Invalid input to parse_path of type: {type(file_path)}')
        return (None, None, None)

    addresses = []  # list of lists, contains bookmarks in files parsed
    file_ages = {}  # dictionary: key = file, value = modification time
    bad_files = []  # files that fail to process
    bookmark_match = re.compile('bookmark')
    for fileNow in files:
        
        if not os.path.exists(fileNow):
                    continue
        
        if bookmark_match.search(fileNow.lower()) is None:
            continue
        
        try:
            (addressSet, soup) = parse_html(fileNow)
            addrLenMax = parsed_max_address_len(addressSet)
        except Exception:
            try:            
                (addressSet, soup) = parse_html(fileNow, ADD_EMPTY=False)
                addrLenMax = parsed_max_address_len(addressSet)                
            except Exception as e:
                print(f'parse_html failed on {fileNow}, error: {e}')
                bad_files.append(fileNow)
                continue
        
        print(f'Parsed: {len(addressSet)}, {addrLenMax}, {fileNow}')
        
        # tag all the html addresses with the current filename
        for i in range(len(addressSet)):
            addressSet[i].append(fileNow)
        
        # extend the set of addresses
        addresses = addresses + addressSet
    
        # get the file age
        file_ages[fileNow] = file_age(fileNow)
    
    return(addresses, file_ages, bad_files)


def stringNChar(STR_IN, N_PRINT):
    """
    Return at least N_PRINT characters or all STR_IN characters of string
    """
    if (len(STR_IN) < N_PRINT):
        return(STR_IN)
    else:
        return(STR_IN[0:(N_PRINT-1)])


def string_remove_emoji(string):
    """
    remove the emoji characters from the passed in string; also removes chinese characters
    and in at least 1 place removed a question mark which was an emoji symbol
    ref: https://gist.github.com/slowkow/7a7f61f495e3dbb7e3d767f97bd7304b

    alternate solution:
        ref: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python/49146722#49146722
        import emoji
        def remove_emojis(text: str) -> str:
            return ''.join(c for c in text if c not in emoji.UNICODE_EMOJI)

    Args:
        string (str): string to remove emojis from
    Returns:
        (str): without emoji characters
    """
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               u"\U00002500-\U00002BEF"  # chinese char
                               u"\U00002702-\U000027B0"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               u"\u2640-\u2642"
                               u"\u2600-\u2B55"
                               u"\u200d"
                               u"\u23cf"
                               u"\u23e9"
                               u"\u231a"
                               u"\ufe0f"  # dingbats
                               u"\u2122"  # trademark symbol
                               u"\u3030"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string)


def stringQuote(X):
    """
    Return input as a quoted string without leading or trailing spaces, newlines or tabs
    """
    X = str(X).strip(' ')
    X = X.strip('\n| |\r|\t')
    X = '"' + X + '"'
    return(X)


def write_address_set(ADDR_SET, ADDR_LEN_MAX, FILENAME):
    """
    Write the address set as a comma separated output to the given FILENAME
    
    Args:
        ADDR_SET (tuple): the data generated by parse_html()
        ADDR_LEN_MAX (int): max length generated by parsed_max_address_len(ADDR_SET)
        FILENAME (str): filename to save to
    Returns:
        returns 0 upon completion
    """
    
    if ADDR_LEN_MAX is None:
        ADDR_LEN_MAX = parsed_max_address_len(ADDR_SET)
    if FILENAME is None:
        FILENAME = 'addr_set.csv'
    
    fHan = open(FILENAME, 'w')
    for addrN in range(0,len(ADDR_SET)):
        addr = ADDR_SET[addrN]
    
        if (len(addr) < ADDR_LEN_MAX):
            fHan.write(','.join(map(stringQuote, addr)) + 
                       ',' * (ADDR_LEN_MAX - len(addr)))
        else:
            fHan.write(','.join(map(stringQuote, addr)))
        fHan.write('\n')
    fHan.close()
    return 0


def debug_parsed_output(ADDR_SET, SOUP, FILENAME_DEBUG):
    """ verify the count
        
    generate reference file with command line
        cat bookmarks.html | sed 's/A HREF/\n/g' | sed 's/<\/A>/\n/g' | 
           grep '=\"' | sed 's/=\" /\"/g' | sed 's/\" /\n/' | sed 's/\"AD/\nAD/' |
           grep '^=\"h' | sed 's/=\"//' > bookmarks_reduced.txt
    which is more accurate than:
        Example creation of test file: 
         grep -i 'a href=' bookmarks_test.html | sed 's/HREF="/HREF=/g' | 
             sed 's/"/\n/g' |  sed 's/HREF/\nHREF/' | grep 'HREF' | 
             sed 's/HREF=//' > bookmarks_test.txt

    """
    
    if FILENAME_DEBUG is None:
        FILENAME_DEBUG = 'bookmarks_reduced2.txt'
    
    #soup = bs.BeautifulSoup(open(fileInputName),"lxml")
    tagSet = SOUP.find_all("a")
    
    if len(ADDR_SET) != len(tagSet):
        # create a dictionary against the shorter variable
        # XXX add a comparison of the ADDR_SET href to the tagSet[i].get('href') and tagset[i].string
        # create a dictionary against ADDR_SET then lookup
        # or vice versa where the dictionary is the shorter object
        if (len(ADDR_SET) < len(tagSet)):
            print(f'should be more tags; some left out? html < soup: {len(ADDR_SET)} < {len(tagSet)}')
            longer = {}
            for addrI in range(0,len(ADDR_SET)):
                # href = string
                longer[ADDR_SET[addrI][1]] = ADDR_SET[addrI][0]
            for tagI in range(0,len(tagSet)):
                # loop across larger set; check if in shorter set; if not print
                if longer.get(tagSet[tagI].get('href')) is None:
                    if tagSet[tagI].string is None:
                        stringName = "None"
                    else:
                        stringName = tagSet[tagI].string
                    if tagSet[tagI].get('href') is None:
                        refName = "None"
                    else:
                        refName = tagSet[tagI].get('href')
                    print(str(tagI) + "::" + stringName + "::" + refName)
                    
        else:
            print(f'where did the extra tags come from? html > soup: {len(ADDR_SET)} > {len(tagSet)}')
            longer = {}
            for tagI in range(0,len(tagSet)):
                # href = string
                longer[tagSet[tagI].get('href')] = tagSet[tagI].string
            for addrI in range(0,len(ADDR_SET)):
                # loop across larger set; check if in shorter set; if not print
                if longer.get(ADDR_SET[addrI][1]) is None:
                    if ADDR_SET[addrI][0] is None:
                        stringName = "None"
                    else:
                        stringName = ADDR_SET[addrI][0]
                    if ADDR_SET[addrI][1] is None:
                        refName = "None"
                    else:
                        refName = ADDR_SET[addrI][1]
                    print(str(addrI) + "::" + ADDR_SET[addrI][0] + "::" + refName)
    
    with open(FILENAME_DEBUG,'r') as fileHan:
        bookmarksReduced = fileHan.readlines()
    bookmarksReduced = [ x.strip() for x in bookmarksReduced ]        
    print(f'Length of bookmarksReduced: {len(bookmarksReduced)}')
    
    if len(ADDR_SET) != len(bookmarksReduced):
        # create a dictionary against the shorter variable
        # XXX add a comparison of the ADDR_SET href to the tagSet[i].get('href') and tagset[i].string
        # create a dictionary against ADDR_SET then lookup
        # or vice versa where the dictionary is the shorter object
        if (len(ADDR_SET) < len(bookmarksReduced)):
            print(f'should be more html; some left out? {len(ADDR_SET)} vs {len(bookmarksReduced)}')
            longer = {}
            for addrI in range(0,len(ADDR_SET)):
                # href = string
                longer[ADDR_SET[addrI][1]] = ADDR_SET[addrI][0]
            deltaFound = 0
            for tagI in range(0,len(bookmarksReduced)):
                # loop across larger set; check if in shorter set; if not print
                if longer.get(bookmarksReduced[tagI]) is None:
                    if bookmarksReduced[tagI] is None:
                        stringName = "None"
                    else:
                        if longer.get(bookmarksReduced[tagI] + "=") is None:
                            # must have stripped trailing = off of some 
                            #   links; add back in to check all are present
                            #   they are; awesome
                            stringName = bookmarksReduced[tagI]
                            if len(stringName) > 200:
                                stringName = stringName[0:200] + '...'
                            deltaFound += 1
                            print(str(tagI) + "::" + stringName)
                    
            print("Found {0} different, {1} html vs {2} soup based set".
                  format(deltaFound, len(bookmarksReduced), len(ADDR_SET)))
        else:
            print('where did the extra tags come from?')
            longer = {}
            for tagI in range(0,len(tagSet)):
                # href = string
                longer[tagSet[tagI].get('href')] = tagSet[tagI].string
            for addrI in range(0,len(ADDR_SET)):
                # loop across larger set; check if in shorter set; if not print
                if longer.get(ADDR_SET[addrI][1]) is None:
                    if ADDR_SET[addrI][0] is None:
                        stringName = "None"
                    else:
                        stringName = ADDR_SET[addrI][0]
                    if ADDR_SET[addrI][1] is None:
                        refName = "None"
                    else:
                        refName = ADDR_SET[addrI][1]
                    print(str(addrI) + "::" + ADDR_SET[addrI][0] + "::" + refName)
    return 0


def test_code(DEBUG=False):
    """
    run test code
    """
    
    print(f'Running bookmarks_parse.py::test_code({DEBUG})')
    pathName = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    # os.chdir(pathName)
    
    if DEBUG:
        fileInputName = 'bookmarks_test.html'
        filedebug = os.path.join(pathName, 'bookmarks_test.txt')
    else:
        fileInputName = 'bookmarks.html'
        filedebug = os.path.join(pathName, 'bookmarks.txt')
    fileInputName = os.path.join(pathName, fileInputName)
    
    (addressSet, soup) = parse_html(fileInputName)
    
    # -- print comma separated output
    addrLenMax = parsed_max_address_len(addressSet)
    write_address_set(addressSet, addrLenMax, os.path.join(pathName, 'addr_set.csv'))
    
    if DEBUG:
        debug_parsed_output(addressSet, soup, FILENAME_DEBUG=filedebug)


if __name__ == '__main__':
    # hardcode to run debugger
    fileInputName = sys.argv[1]
    (addressSet, soup) = parse_html(fileInputName, DEBUG=True)
    print('bookmarks_parse.py direct call. Change to parse and dump csv list?')
    test_code(DEBUG=True)
            
