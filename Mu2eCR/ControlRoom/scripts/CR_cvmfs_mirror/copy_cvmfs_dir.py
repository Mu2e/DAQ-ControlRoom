#!/usr/bin/env python

import os
import sys
import shutil
import errno

def copyanything(src, dst):
    if os.path.exists(dst):
        print "### WARNING! destination folder exists, skipping!\n"
        return
    try:
        shutil.copytree(src, dst, symlinks=True)
    except OSError as exc: # python >2.5
        if exc.errno == errno.ENOTDIR:
            shutil.copy(src, dst)
        else: raise
    return

# get list of dirs from input file

if len(sys.argv) != 4:
    print "usage: copy_cvmfs_dir.py list.txt exclude_dir.txt dest_dir"

input_list = sys.argv[1]

exclude_list = sys.argv[2]

dest_root_dir = sys.argv[3]

exclude_dir=[]
with open(exclude_list, 'r') as inlist:
    for iline in inlist:
        exclude_dir.append(iline.strip())

with open(input_list, 'r') as inlist:
    for iline in inlist:
        isrc = iline.strip()
        if not isrc:
            continue
        skip = False
        for i in exclude_dir:
            if i in isrc:
                skip = True
        if skip:
            print "skipping directory: {}".format(isrc)
            continue
        idest = os.path.join(dest_root_dir, os.path.relpath(isrc, '/cvmfs'))
        #idest = os.path.dirname(idest)
        print "{} --> {}".format(isrc, idest)
        copyanything(isrc, idest)
