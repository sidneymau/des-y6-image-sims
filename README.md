# DES Y6 Image Sims

utilities, scripts, and configs for running [eastlake](https://github.com/des-science/eastlake) for the DES Y6 image simulations

## tiles

`run-query.sh` -- query easyaccess for tiles
```
bash tiles/run-query.sh -f tiles-y6.txt
```

## meds

`run-download.sh` -- download meds for tiles via rsync
```
bash meds/run-download.sh -f tiles-y6.txt
```

## eastlake

`test.sh` -- quickly test a config
```
bash eastlake/test.sh -c configs/grid-bright/config.yaml -t DES2205+0126 -s $RANDOM
```

`run.sh` -- run a full simulation pair
```
sbatch eastlake/run.sh -c configs/grid-bright/config.yaml -t DES2205+0126 -s $RANDOM
```

`run-all.sh` -- run a full simulation pair for all tiles
```
bash eastlake/run-all.sh -c configs/grid-bright/config.yaml -f tiles-y6.txt -s $RANDOM
```

`resume.sh` -- resume a simulation pair with a checkpoint (i.e., from a failed job)
```
sbatch eastlake/resume.sh -c configs/grid-bright/config.yaml -t DES2205+0126 -s $RANDOM
```

`resume-all.sh` -- resume or rerun all simulation pairs that do not have a metadetect catalog output
```
bash eastlake/resume-all.sh -c configs/grid-bright/config.yaml
```

## analysis

`compute_bias.py` -- compute multiplicative and additive shear bias for output sims
```
python analysis/compute_bias.py $SCRATCH/y6-image-sims/grid-bright --seed $RANDOM
```
