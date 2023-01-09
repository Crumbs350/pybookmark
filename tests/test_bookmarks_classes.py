#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bookmark_class tests

note pytest only runs against function if it is named test_*() not *_tests()

@author: Crumbs
"""

import datetime
from pybookmark.bookmarks_class import AgeAsInt, bookmarkAttr, bookmarks
    
def test_AgeAsInt():
    a = AgeAsInt(5)
    b = AgeAsInt(5)
    assert a == b
    
    assert a.get_datetime() == b.get_datetime()
    assert a.get_time_str() == b.get_time_str()
    
    a.set_by_datetime(datetime.datetime(1970, 12, 31, 18, 0, 5))
    assert a != b
    assert a > b
    assert a >= b
    assert b < a
    assert b <= a
    b.set_by_datetime(datetime.datetime(1970, 12, 31, 18, 0, 5))
    assert a == b
    assert a >= b
    assert a <= b    

def bookmark_attr_reference():
    """ define reference bookmark attributes as a list with only 1 value each
        0:'label',
        1:'age',
        2:'tags',
        3:'location',
        4:'description',
        5:'file location',
    """
    ref_bookmark = [
        ['the label'],
        [AgeAsInt(1e6)],
        ['some tags'],
        ['location string'],
        ['descriptive string'],
        ['where file?']
        ]
    return ref_bookmark


def bookmark_attr_reference2():
    """ define reference bookmark attributes as a list
        0:'label',
        1:'age',
        2:'tags',
        3:'location',
        4:'description',
        5:'file location',
    """
    ref_bookmark = [
        ['category tag: awesome bookmark '],  # extra space on purpose to test
        [AgeAsInt(1e8)],
        ['link', 'python'],          # duplicate tags to test
        ['category::sub-category'],  # note :: division
        ['descriptive string'],
        []
        ]
    return ref_bookmark


def test_bookmark_attr():
    ref_bookmark = bookmark_attr_reference()
    x = bookmarkAttr(ref_bookmark)

    # - test reference dictionary, hardcoded so if changes know class changed
    assert x.bookmark_map_forward[0] == 'label'
    assert x.bookmark_map_forward[1] == 'age'
    assert x.bookmark_map_forward[2] == 'tags'
    assert x.bookmark_map_forward[3] == 'location'
    assert x.bookmark_map_forward[4] == 'description'
    assert x.bookmark_map_forward[5] == 'file location'
    
    assert x.bookmark_map_reverse['label'] == 0
    assert x.bookmark_map_reverse['age'] == 1
    assert x.bookmark_map_reverse['tags'] == 2
    assert x.bookmark_map_reverse['location'] == 3
    assert x.bookmark_map_reverse['description'] == 4
    assert x.bookmark_map_reverse['file location'] == 5
    
    # - test direct values as assigned, and by get_value; handle age separately
    assert ref_bookmark[0] == x.get_value('label')
    assert ref_bookmark[0] == x[0]

    assert ref_bookmark[2] == x.get_value('tags')
    assert ref_bookmark[2] == x[2]

    assert ref_bookmark[3] == x.get_value('location')
    assert ref_bookmark[3] == x[3]

    assert ref_bookmark[4] == x.get_value('description')
    assert ref_bookmark[4] == x[4]

    assert ref_bookmark[5] == x.get_value('file location')
    assert ref_bookmark[5] == x[5]
    
    # - test direct age values as assigned, and by get_value;
    # age is forced to AgeAsInt and get_value returns non-list
    # assert ref_bookmark[1][0] == x.get_value('age')
    #   fails because somehow eq test gets called twice against other object
    #   first as AgeAsInt, then as float which fails the instance test
    #   therefore manually confirm equality
    # was getting called twice by multiple calls to AgeAsInt on same value so
    #   class of self.value was AgeAsInt(AgeAsInt), etc
    # which meant assert z == y failed because
    #   z below returned as type float
    #   y below returned as type AgeAsInt
    # now that bookmark_class.set_value is fixed both return type float as expected
    assert str(ref_bookmark[1][0]) == str(x.get_value('age')) # half ass hack to verify value is the same
    assert type(ref_bookmark[1][0]) == type(x.get_value('age'))
    
    z = ref_bookmark[1][0].get_value()    
    y = (x.get_value('age')).get_value()
    assert z == y

    # assert ref_bookmark[1] == x.get_value('age', age_drop_list=False)
    for index in range(len(ref_bookmark[1])):
        assert ref_bookmark[1][index] == x.get_value('age', age_drop_list=False)[index]
    
    assert ref_bookmark[1] == x[1]
    
    # - test get_array
    assert x.get_array() == ref_bookmark
    
    # - test get_dict
    xd = x.get_dict()
    for key_index in x.bookmark_map_forward:
        assert xd[x.bookmark_map_forward[key_index]] == ref_bookmark[key_index]

    # - test set_array_keys, must assign then confirm values match
    ref_bookmark_dict = {}
    for key_index in x.bookmark_map_forward:
        ref_bookmark_dict[x.bookmark_map_forward[key_index]] = ref_bookmark[key_index]
    y = bookmarkAttr(())
    y.set_array_keys(**ref_bookmark_dict)
     
    assert ref_bookmark[0] == y.get_value('label')
    assert ref_bookmark[0] == y[0]

    assert ref_bookmark[1][0] == y.get_value('age')
    assert ref_bookmark[1] == y[1]
    for index in range(len(ref_bookmark[1])):
        assert ref_bookmark[1][index] == y.get_value('age', age_drop_list=False)[index]
   
    assert ref_bookmark[2] == y.get_value('tags')
    assert ref_bookmark[2] == y[2]

    assert ref_bookmark[3] == y.get_value('location')
    assert ref_bookmark[3] == y[3]

    assert ref_bookmark[4] == y.get_value('description')
    assert ref_bookmark[4] == y[4]

    assert ref_bookmark[5] == y.get_value('file location')
    assert ref_bookmark[5] == y[5]
    
    assert ref_bookmark_dict == y.bookmark_list_to_dict(ref_bookmark)
    
    # - test setting values, append + dropping to unique mixed type list
    value_add = 65
    x.set_value('label', value_add)
    ref_bookmark[0].append(value_add)
    assert x.get_value('label') == ref_bookmark[0]
    
    x.unique()
    expected_value = list(set(ref_bookmark[0]))
    sorted(expected_value, key=lambda x: str(x))
    assert x.get_value('label') == expected_value

    # - test setting values with overwrite
    ref_bookmark = bookmark_attr_reference()
    x.set_value('label', ref_bookmark[0], overwrite=True)
    assert x.get_value('label') == ref_bookmark[0]
    
    # - test setting values with overwrite to verify strip
    ref_bookmark = bookmark_attr_reference()
    space_value = ' extra spaces '
    x.set_value('label', space_value, overwrite=True)
    space_value = space_value.strip()
    assert x.get_value('label') == [space_value]
    
    # - test setting values list unique (None is dropped)
    some_list = ['word', 'word2', 'word3', None, 'word5'] 
    expected_value = [x for x in x[2] + some_list if x is not None]
    x.set_value('tags', some_list)
    assert x[2] == expected_value
    assert x.get_value('tags') == expected_value
    
    # - test setting values list not unique, made unique
    ref_bookmark = bookmark_attr_reference()
    x = bookmarkAttr(ref_bookmark)
    some_list = ['word', 'word', 'word2', 'word3', None, 'word5']
    expected_value = [] # need to drop duplicate, in same order, and None values
    for xnow in x[2] + some_list:
        if xnow is None or xnow in expected_value:
            continue
        expected_value.append(xnow)
    x.set_value('tags', some_list)
    assert x[2] == expected_value
    assert x.get_value('tags') == expected_value
    
    # - test drop
    some_list = ['word', 'word', 'None', 'word3', None, 'word5', '', 'word5']
    x.set_value('tags', some_list, overwrite=True)
    drop_list = ['', 'None', None, 'word']
    x.remove_values(drop_list)
    expected_value = [x for x in some_list if x not in drop_list]
    assert x.get_value('tags') == expected_value
    
    # - test unique
    some_list = ['word', 'word', 'None', 'word3', 'word5', '', 'word5']
    x.set_value('tags', some_list, overwrite=True)
    x.unique()
    expected_value = list(set(some_list))
    expected_value.sort()
    assert x.get_value('tags') == expected_value
    
    # - testing drop down
    ref_bookmark = bookmark_attr_reference2()
    x = bookmarkAttr(ref_bookmark)
    

def test_bookmark():
    # if 0: # XXX manual until figure out pytest path handling
    # - test reading, building, and write
    file_use = 'data/addr.json'
    file_out = 'data/addr_write_compare.json'
    bb = bookmarks()
    bb.read_json(file_use)

    b = bookmarks.Address_Struct_Read(file_use)
    
    assert b == bb
    
    # must run this test comparison manually unless do something complex like checksum on files which will fail,
    # minor difference, age non-list vs list
    bb.write_json(file_out)

    # - test build_address_struct: build from addresses list by 
    #       could converting bookmark_attr to list and insert url + dead lists
    #       safer to use function to build values
    #   do NOT introduce lists into attributes or asserts will fail because
    #       addresses method is not designed to handle attribute lists,
    #       it handles attribute lists of single values per attribute 
    addresses = []
    url_set = []       # used to track urls used to apply tests
    bookmark_set = []  # used to track bookmarks defined to apply tests
    
    url_now = 'http://ref_book2'
    bookmark1 = bookmarkAttr(bookmark_attr_reference())
    addresses.append(bookmarks.Address_List_Converter(
        url_now, bookmark1))
    url_set.append(url_now)
    bookmark_set.append(bookmark1.copy())
    
    # different url, tags, and location
    url_now = 'http://python.howto_prog.com'
    bookmark1.set_value('tags', 'different_tag', overwrite=True)
    bookmark1.set_value('location', 'programming::python', overwrite=True)
    addresses.append(bookmarks.Address_List_Converter(
       url_now, bookmark1))
    url_set.append(url_now)
    bookmark_set.append(bookmark1.copy())
    
    # differs by url only
    url_now = 'http://not_python.howto_prog.com'
    bookmark1 = bookmarkAttr(bookmark_attr_reference())
    addresses.append(bookmarks.Address_List_Converter(
       url_now, bookmark1))
    url_set.append(url_now)
    bookmark_set.append(bookmark1.copy())

    bb = bookmarks()
    bb.build_address_struct(addresses)
    
    # now test length and values = input bookmark attributes
    assert len(bb) == len(addresses)
    for index in range(len(addresses)):
        assert bb[url_set[index]] == bookmark_set[index]

    # - test add
    len_now = len(bb)
    url_now = 'http://different.com'
    bb.add(url_now, bookmark1)
    assert len(bb) == (len_now + 1)
    assert bb[url_now] == bb[url_set[-1]]
    
    # - test delete
    bb.delete(url_now)
    assert len(bb) == len_now
    assert url_now not in bb.keys()        
    
    # - test replace: assign url 1 to have same bookmark attributes as url 0
    #   verify unequal before and equal after
    assert bb[url_set[0]] != bb[url_set[1]]
    bb.replace(url_set[1], bookmark_set[0])
    assert bb[url_set[0]] == bb[url_set[1]]    
    
    # - test search
    # XXX
    
    # - test clean: clean_address_struct
    
    # - test unique

def bookmark_test_dev_code():
    # these are development tests not intended to be automated
    x = bookmarkAttr((6,5,[5,5],6,[1,2]))

    x = bookmarkAttr((5,4,2))
    x.get_dict()
    x.get_array()
    x.set_value('file location','tgz')
    x.set_value('label','pajamas')
    x.set_value(1, None)
    x.get_dict()
    x.set_value(1, [32, None, 64])
    x.get_array()
    x
    x.set_array_keys(**{'label': 32, 'age': 343, 'tags': 'king james', 'file location': ['tgz']})
    x
    x.set_value('label','horse', overwrite=True)
    x
    x.set_value('label', 'gamma')
    x.set_value('label', 'horse')
    x
    x.unique()
    x
    
    x1 = bookmarkAttr(())
    x1.set_array_keys(**{'label': 32, 'age': 343, 'tags': 'king james', 'file location': ['tgz']})
    
    # xxx should be asserts or real tests    
    x = intAge(5)
    print(f'{x.get_datetime()}')
    print(f'{x.get_time_str()}')
    x.set_by_datetime(datetime.datetime(1970, 12, 31, 18, 0, 5))
    print(f'{x}')
    print(f'{x.get_time_str()}')
    x.dump()
    dir(x)
    
    x = AgeAsInt(5)
    print(f'{x.get_datetime()}')
    print(f'{x.get_time_str()}')
    x.set_by_datetime(datetime.datetime(1970, 12, 31, 18, 0, 5))
    print(f'{x}')
    print(f'{x.get_time_str()}')
   
    y = bookmarks()
    url_test = 'https://356.com'
    y.add(url_test, x1)
    # assert len(list(y.keys())) == 1
    y.add(url_test, x1)  # this should error XXX
    y.delete(url_test)
    # assert len(list(y.keys())) == 0
    y.add(url_test, x1)
    y.keys()
    # assert y[url_test] == x1
    
    addresses = [
        ['link name', 'https://link1.com', 23, [], [], [], 'tag', 'desc', 'fl'],
        ['link 2', 'https://link2.com', 25, [], [], [], 'tags', 'desc2', 'fl2'],
        ['link 3', 'https://link3.com', 26, [], [], [], 'tag3', 'desc3', 'fl3'],
        ['link 4', 'https://link4.com', 34, [], [], [], 'tag4', 'desc4', 'fl4']
       ]
    bd = bookmarks()
    bd.build_address_struct(addresses)
    bd['https://link4.com']
    bd['https://link4.com'].get_dict()
    

def bookmark_test_json_print_ba():    
    """ this shows that the print with the new class is equivalent to before """
    x2 = bookmarkAttr(())
    x2.set_array_keys(**{'label': 34, 'age': 345, 'tags': 'queen', 'file location': ['tgz']})
    y = {'url1':x1, 'url2':x2}
    filename = '/home/darkknight/Documents/temp/bookmark_test_json1.json'
    with open(filename, 'w') as fJson:
        json.dump(y, fJson, indent=2)