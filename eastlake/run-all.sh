#!/bin/bash

while getopts 'c:f:s:n:' opt; do
	case $opt in
		(c) config=$OPTARG;;
		(f) filename=$OPTARG;;
		(s) seed=$OPTARG;;
		(n) njobs=$OPTARG;;
	esac
done

if [[ ! $config ]]; then
	printf '%s\n' "No config specified. Exiting.">&2
	exit 1
fi
echo "config:	$config"

if [[ ! $filename ]]; then
	printf '%s\n' "No file specified. Exiting.">&2
	exit 1
fi
echo "file:	$filename"

if [[ ! $seed ]]; then
	printf '%s\n' "No seed specified. Exiting.">&2
	exit 1
fi
echo "seed:	$seed"
RANDOM=$seed

if [[ ! $njobs ]]; then
	njobs=$(wc -l < $filename)
fi
echo "njobs:	$njobs"

submitted="${filename%.*}-$(basename $(dirname $config))-submitted.txt"
touch $submitted
for tile in $(comm -23 <(sort $filename) <(sort $submitted) | shuf | head -n $njobs)
do
	seed=$RANDOM
	echo "sbatch eastlake/run.sh -c $config -t $tile -s $seed"
	sbatch eastlake/run.sh -c $config -t $tile -s $seed
	echo $tile >> $submitted
done
echo "finished submitting jobs"
