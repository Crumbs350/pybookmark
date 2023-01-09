#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
use pybookmark.pybookmarkjsonviewer to view and manage bookmarks

runs from current path ie assumes all data files are in the current path
assumes yaml file is local too

example:
    $ cd __data_path__
    $ python PyBookmark_viewer.py

@author: Crumbs
"""

import os
import yaml
import pybookmark.pybookmarkjsonviewer as pyb
import pybookmark.support as support


if __name__ == '__main__':
    config_f = os.path.join(os.path.abspath(os.path.curdir), 'pybookmark_viewer.yaml')

    assert os.path.exists(config_f)
    with open(config_f, 'r') as fHan:
        config_args = yaml.safe_load(fHan)
    # file (str)
    # load_newest (boolean)
    # output_dir (str)
    # width (int)
    # height (int)

    file_use = config_args['file']

    if 'output_dir' in config_args:
        output_dir = config_args['output_dir']
    else:
        output_dir = os.path.abspath(os.path.curdir)

    initial_dir = os.path.dirname(file_use)
    if len(initial_dir) == 0:
        initial_dir = os.path.abspath(os.path.curdir)
    
    # set viewer geometry
    height = width = 800
    if 'width' in config_args:
        width = config_args['width']
    if 'height' in config_args:
        height = config_args['height']
        
    if config_args['load_newest']:
        file_use = support.addr_newest(file_use)
    pyb.view_data(json_file = file_use,
                  initial_dir = initial_dir,
                  output_dir = output_dir, 
                  width = width, 
                  height = height,
                  config = config_args)
