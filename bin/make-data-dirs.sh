#!/usr/bin/env python
# Script to make the different data areas for the Mu2eDAQ setup
#
# We provide this script so that everything is consistant
# across nodes in the clusters

import sys
import os
import json

# First specify the prefix lists
prefixList = ["data","data-2","test-data","scratch"]
runtype = ["test","prod","commissioning","study","other"]
detectorList = ["calo","trk","crv","stm","extmon","aux","other"]

# Make the primary data areas:
#
for thePrefix in prefixList :
    for theType in runtype :
        for theDet in detectorList :
            thePath = "/" + thePrefix + "/" + theType + "/" + theDet "/"
            try:
                os.makedirs(thePath, exist_ok=True)
                print(f"Directory '{thePath}' created successfully.")
            except Exception as e:
                print(f"Error creating directory: {e}")
