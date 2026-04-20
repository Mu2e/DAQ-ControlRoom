#!/usr/bin/env python

import sys

if len(sys.argv) != 2:
    print("usage: modify_env.py path_to_env_file")

filter_list = ['HOSTNAME', 'TERM', 'PWD', 'SHLVL', 'HOME', 'LESSOPEN', '_',
               'REFRESHED_AT', 'LS_COLORS']
with open(sys.argv[1], 'rw') as efile:
    for i in efile:
        i = i.strip()
        j = i.split('=', 1)
        if j[0] in filter_list:
            continue
        inew = "export " + j[0] + '='
        if j[1]:
            inew += '"' + j[1] + '"'
        else:
            inew += '""'
        print(inew)
