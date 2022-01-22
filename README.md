# PyBookmark
A bookmark.html parser, merger and viewer using pure python
* parse bookmark.html files from browsers with html structure included
* merge the parsed bookmark.html files
* export the parsed and merged bookmarks as a JSON archive
* GUI to view, edit, and add to the bookmarks stored in JSON archive

# Package Justification
PyBookmark exists to solve a problem you may not have. Read the following to understand the trade off.

## Why
You should use PyBookmark if:
* you have many different bookmark html files saved over time
* you wish to merge your bookmark history from multiple computers or files into one view
* you wish to separate the bookmark manager from the browser
  - reduce possibility for tracking fingerprint (what bookmarks exist, unique icon file checksums or URLs)
* you wish to reduce clutter in bookmarks (icons)
* you are tired of Firefox (or other) changing which fields are supported to edit/view
  - example: description, keywords, tags are intermittently viewable
* you are tired of Firefox (or other) breaking or changing how bookmark edit occurs
  - example: recently Firefox made it so edits in the bookmark organizer did not save
* you want a more powerful bookmark search method
* you like control

## Why Not
You should not use PyBookmark if:
* you are happy with native browser bookmark management
* you have very few bookmarks or all your bookmarks are in one file already
* you need or want in application multiple device synchronization or cloud backup support
* you primarily browse the internet using a smartphone or proprietary platform apps (facebook/reddit)
* you do not use bookmarks (why did you read this far?)
* you have no interest in understanding code or data structure
  - eventually a browser change will mean the file format you try to import won't work and you will have to figure out why

# Implementation Details
## Assumptions
1. Bookmark data is stored in html format. It is possible to extend to merge in json and other backups but that has not been the focus.
2. Bookmark data has additional folder structure that
  - is important
  - indicates relationships between bookmarks
  - these assumptions are why a complex parsing of beautiful soup is implemented to extract the URLs and related content
3. Colons are useful separators of descriptive location in bookmark labels (not the URL)
4. Duplicate bookmarks are bad but merging should be controlled
5. You intend to migrate to a separate bookmark manager
6. You will always be on a platform that can read the output json structure

## Run Options (How to Use)
1. parse single file
   * library: pybookmark.bookmarks_parse.py
2. merge files
   * scripts: scripts.bookmarks_merge.py
   * parses single or multiple bookmark.html files using pybookmark.bookmarks_parse.py library
   * merges bookmarks across html files
   * reduces duplication of information based on user defined mappings
   * you only need to do this once if you start using the viewer as your bookmark manager
3. viewer: 
   * viewer allows view, edit, add/remove of json bookmark collection
   * library: pybookmark.pybookmarkjsonviewer.py
     - can be called from command line
     - $ python pybookmarkjsonviewer.py -f /path_to_json_file/sample.json
   * script: scripts.PyBookmark_viewer.py
     - runs against predefined yaml configuration in the same path
   * Uses Tk to provide GUI
   * note to run from a desktop launcher in linux may require a separate shell script with interactive mode enabled see [reference](https://forums.linuxmint.com/viewtopic.php?p=2127717#p2127717)

## File Layout
* Data contains
  - reference YAML configurations
  - example input bookmark.html files
  - example output json files
* pybookmark
  - where the library code is, see run options above for types
  - where the icon file is
* scripts
  - where command line tools live
  - see run options above for more details

## Data Structures

The core data structure is AddrStruct.  
  addrStruct: dictionary of url keys with list of list values  
     key = URL address  
     [0] = label  
     [1] = age  
     [2] = tags  
     [3] = location  
     [4] = description  
     [5] = file location  

##  Requirements Overview
Created using Python 3.7 or higher and Beautiful Soup 4.
