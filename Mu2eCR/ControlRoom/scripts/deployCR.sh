#!/bin/sh 

# a script to deploy control room directories

# It will only deploy directly under the current directory. 
# There's a bootstrap issue with CVS, so the best way to run it is just by
# copying from another node, or grabbing from the CVS web interface, and running it.


loglev=1
dbglev=2

dbg_message () {
        if [ $loglev -ge $dbglev ]; then
                echo $1
        fi
}

usage () {
        echo "" >&2
        echo "usage: `basename $0` [options]" >&2
        echo "options:" >&2
        echo "    -h        : prints this usage message" >&2
        echo "    -d <detector> [NDOS]: specifies the detector" >&2
        echo "    -t <target> [bin DAQ-Desktop-Utilities Desktop .mozilla .s3producer graphics]: specifies the targets" >&2
        echo "                to deploy (multiples work in the default, but only a single" 
        echo "                target can be specified on the command line)"
        echo "    -m <target machine> [HOSTNAME] (no domain): specifies which hosts files " >&2
        echo "                to deploy" >&2
        echo "    -u        : do a cvs update"
        exit
}

set_defaults () {
        detector="NDOS"
        target_list="bin Desktop DAQ-Desktop-Utilities .mozilla .s3producer graphics"
        source_machine=`echo $HOSTNAME| sed -e "s#\..*##g"`
        package=NovaControlRoom
        tmppackage=tmp_$package.$$
        cvsroot=:pserver:anonymous@cdcvs.fnal.gov:/cvs/nova
}

process_args () {
        while getopts "hut:m:d:-:" opt; do
                dbg_message "initial: opt=$opt"
                if [ "$opt" = "-" ]; then
                        opt=$OPTARG
                        dbg_message "check for -: opt=$opt"
                fi
                dbg_message "case block: opt=$opt, OPTARG=$OPTARG"
                case $opt in
                        h | help)
                                usage
                                ;;
                        u | update)
                                do_cvs_update=yes
                                ;;
                        t | target)
                                target_list="$OPTARG"
                                ;;
                        m | machine)
                                source_machine=$OPTARG
                                ;;
                        d | detector)
                                detector=$OPTARG
                                ;;
                        *) usage
                        ;;

                esac
        done

        dbg_message "machine=$source_machine"
}

checkout () {

        # checkout a temporary copy of the NovaControlRoom package
        cvs -Q -d $cvsroot co -d $tmppackage $package

}

cleanup () {

        # remove temporary package
        \rm -fr $tmppackage

}

update_target () {

        local target=$1
	local odir=$PWD
        if [ "x$do_cvs_update" != "x" ]; then
                echo "Now will do a CVS update in $target"
		cd $target
                cvs update 
		cd $odir
        else
                echo "Skipping CVS update in $target - that's up to you"
        fi
}

existing_dir () {

        local source=$1
        local target=$2

        echo "Target $target exists"

	# get list of CVS directories in source
	olddir=`pwd`
	cd $source
	cvsdirs=`find . -name CVS`
	dbg_message "cvsdirs=$cvsdirs"

	# copy each of them, if need be
	for dir in $cvsdirs; do
		cd $olddir
		if [ ! -e $target/$dir ]; then
			echo "CVS Directory is missing in $target/$dir.  Will create."
			dbg_message "echo cd $source"
			cd $source
                	dbg_message "echo cp -r --parents $dir $olddir/$target"
                	cp -r --parents $dir $olddir/$target
			dbg_message "echo cd $olddir"
			cd $olddir
		else
                	echo "CVS Directory exists in $target/$dir ."
		fi

	done
}

new_dir () {

        local source=$1
        local target=$2

        echo "Target $target does not exist.  Making new copy."
        dbg_message "cp -r $source $target"
        cp -r $source $target
}

do_targets () {

        for target in $target_list
        do
                echo " "
                echo "Target: $target"
                local full_source=$tmppackage/$target/$detector/$source_machine
                if [ -e $full_source ]; then
                        if [ -e $target ]; then
                                existing_dir $full_source $target
                        else
                                new_dir $full_source $target
                        fi
                        update_target $target
                else
                        echo "$target does not appear to exist in repository for"
                        echo "    $detector/$source_machine."
                fi
        
        done
}


main () {

        set_defaults
        process_args $*
        checkout
        do_targets
        cleanup

}

main $*

