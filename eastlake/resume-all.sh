#!/bin/bash

while getopts 'c:' opt; do
	case $opt in
		(c) config=$OPTARG;;
	esac
done

if [[ ! $config ]]; then
	printf '%s\n' "No config specified. Exiting.">&2
	exit 1
fi
echo "config:	$config"

run=$(basename $(dirname $config))
for tile in $(ls $SCRATCH/y6-image-sims/$run)
do
	for seed in $(ls $SCRATCH/y6-image-sims/$run/$tile)
	do
		pmdetcat=${SCRATCH}/y6-image-sims/${run}/${tile}/${seed}/plus/des-pizza-slices-y6/${tile}/metadetect/${tile}_metadetect-config_mdetcat_part0000.fits
		mmdetcat=${SCRATCH}/y6-image-sims/${run}/${tile}/${seed}/minus/des-pizza-slices-y6/${tile}/metadetect/${tile}_metadetect-config_mdetcat_part0000.fits
		if [[ (! -f $pmdetcat) || (! -f $mmdetcat) ]]; then
			pjobrecord=${SCRATCH}/y6-image-sims/${run}/${tile}/${seed}/plus/job_record.pkl
			mjobrecord=${SCRATCH}/y6-image-sims/${run}/${tile}/${seed}/minus/job_record.pkl
			if [[ (-f $pjobrecord) && (-f $mjobrecord) ]]; then
			    echo "sbatch eastlake/resume.sh -c $config -t $tile -s $seed"
			    sbatch eastlake/resume.sh -c $config -t $tile -s $seed
			else
			    echo "sbatch eastlake/run.sh -c $config -t $tile -s $seed"
			    sbatch eastlake/run.sh -c $config -t $tile -s $seed
			fi
		fi
	done
done