#!/bin/bash

if [ "$#" == "0" ]; then
  exit 1
fi

CR_version=$1
mkdir -p /scratch/cvmfs
dir_file=/scratch/dirs_${CR_version}.txt
env_file=/scratch/cvmfs/setup_${CR_version}.sh

cd /scratch

source /cvmfs/nova.opensciencegrid.org/novasoft/slf6/novasoft/setup/setup_nova.sh -b maxopt -r ${CR_version}
[[ -z "$GIT_DIR" ]] &&  export GIT_DIR=${GIT_HOME}

# make dirs.txt
rm -f ${dir_file}
touch ${dir_file}
for i in `ups active| awk '{print $1}'| tr [a-z] [A-Z]`
do
	j=${i}_DIR
	echo ${!j} >> ${dir_file}
done

echo "/cvmfs/nova.opensciencegrid.org/novasoft/slf6/novasoft/releases/${CR_version}" >> ${dir_file}

# make env file
printenv > /scratch/env_tmp.sh

# modify env file
/scratch/modify_env.py /scratch/env_tmp.sh > ${env_file}

# append ups functions to env file
declare -f >> ${env_file}

rm -f /scratch/env_tmp.sh

/scratch/copy_cvmfs_dir.py  ${dir_file} dirs_exclude.txt /scratch/cvmfs
