# **Database for ML or MVLR**

### Author: Zihao Ye

### CreateDate: 2023-02-14

### Version: 2023-04-18

## **Introduction**

This is a automatic database generator and discriptor extractor for ML or MVLR.
Currently, it is aimed at TS structure based learning.

## **Framework**

### *Database generator*

1. read all raw structures from ZS-CMJ/rawmodel  
TODO: delete certain data

2. generate inp file of DFT-mod, xtb-mod, xtb-fixmod, gauxtb-mod based on model files or rules provided  
TODO: generate conformation search input file

3. submit(gau) or run(xtb) jobs  

### *Discriptor extractor*

0. all data should be ready according to `Database structure` by now  

1. read all raw structures from ZS-CMJ/rawmodel, generate class, which provides methods to get data needed  
TODO: read ee value, yield, reaction contiditions etc. from csv  
TODO: read from hdf5 and recreate class, which can add new data to  

2. extract data specified by user and add to tmp data  

3. generate csv files and input data for pytorch at command 

#### version 0.1

mainly realize extract global data/feature  
output data into csv file  

### *Dataloader*

read csv file  
reconstruct according to job type (currently only ee%)  
and load data into pytorch  

## **Database structure**

```
Database/  # root database directory
    ZS-CMJ/  # project ZS-CMJ
        generator.py  # script of database generator
        extractor.py  # script of discriptor extractor
        expdata.csv  # all experimental data collected in csv format
        runxtb.py  # script of xtb job submittion
        batchgjf.py  # script of file generation

        utils/  # inp and model files
            gaumodel.gjf  # optional, used in DFT-mod
            gauxtbmodel.gjf  # optional, used in gauxtb-mod
            gauspmodel.gjf  # optional, used in *-gau-sp
            constrain.inp  # optional, used in xtb-mod
            fix.inp  # optional, used in xtb-fixmod
            extderi  # used in gauxtb submit
            genxyz  # used in gauxtb submit
            xtb.sh  # used in gauxtb submit

        rawmodel/  # raw models, structures without optimiaztion
            Xu01-1a-2a-major.gjf  # labels seperated by '-'
            Xu01-1a-2a-minor.gjf
            Xu02-1a-2a-major.gjf
            Xu02-1a-2a-minor.gjf
            ...

        DFT-mod/  # DFT modredundant optimized results
            log/  # log files
                Xu01-1a-2a-major-gau.log
                Xu01-1a-2a-minor-gau.log
                Xu02-1a-2a-major-gau.log
                Xu02-1a-2a-minor-gau.log
                ...
            fchk/  # fchk files
                Xu01-1a-2a-major-gau.fchk
                Xu01-1a-2a-minor-gau.fchk
                Xu02-1a-2a-major-gau.fchk
                Xu02-1a-2a-minor-gau.fchk
                ...
            Xu01-1a-2a-major-gau.gjf  # calculation input file
            ...

        xtb-mod/  # xtb modredundant(constrain) optimized results
            constrain.inp  # constrain inp file
            Xu01-1a-2a-major-xtb.xyz  # input xyz file
            Xu01-1a-2a-major-xtb-out.xyz  # output xyz file
            Xu01-1a-2a-major-xtb.charges  # charge file
            Xu01-1a-2a-major-xtb.wbo  # wiberg bond order file
            Xu01-1a-2a-major-xtb.log  # log file
            ...

        xtb-fixmod/  # xtb modredundant(fix) optimized results
            fix.inp  # fix inp file
            Xu01-1a-2a-major-xtbfix.xyz  # input xyz file
            Xu01-1a-2a-major-xtbfix-out.xyz  # output xyz file
            Xu01-1a-2a-major-xtbfix.charges  # charge file
            Xu01-1a-2a-major-xtbfix.wbo  # wiberg bond order file
            Xu01-1a-2a-major-xtbfix.log  # log file
            ...

        gauxtb-mod/  # xtb modredundant(constrain) optimized results, invoked by gaussian
            log/  # log files
                Xu01-1a-2a-major-gauxtb.log
                Xu01-1a-2a-minor-gauxtb.log
                Xu02-1a-2a-major-gauxtb.log
                Xu02-1a-2a-minor-gauxtb.log
                ...
            fchk/  # fchk files
                Xu01-1a-2a-major-gauxtb.fchk
                Xu01-1a-2a-minor-gauxtb.fchk
                Xu02-1a-2a-major-gauxtb.fchk
                Xu02-1a-2a-minor-gauxtb.fchk
                ...
            Xu01-1a-2a-major-gauxtb.gjf  # calculation input file
            
        TODO: DFT-mod-gau-sp/
        
        gauxtb-mod-gau-sp/  # gaussian singlepoint calculation results, based on gauxtb modredundant(constrain) optimized results, invoked by gaussian
            log/
                Xu01-1a-2a-major-gauxtbgausp.log
                Xu01-1a-2a-minor-gauxtbgausp.log
                Xu02-1a-2a-major-gauxtbgausp.log
                Xu02-1a-2a-minor-gauxtbgausp.log
                ...
            fchk/
                Xu01-1a-2a-major-gauxtbgausp.fchk
                Xu01-1a-2a-minor-gauxtbgausp.fchk
                Xu02-1a-2a-major-gauxtbgausp.fchk
                Xu02-1a-2a-minor-gauxtbgausp.fchk
                ...
            Xu01-1a-2a-major-gauxtbgausp.gjf  # calculation input file
            ...

        xtb-mod-xtb-sp/  # xtb singlepoint calculation results, based on xtb modredundant(constrain) optimized results
            Xu01-1a-2a-major-xtb-sp.xyz  # input xyz file
            Xu01-1a-2a-major-xtb-sp.log  # log file
            Xu01-1a-2a-major-xtb-sp.charges  # charge file
            Xu01-1a-2a-major-xtb-sp.wbo  # wiberg bond order file
            ...

        xtb-fixmod-xtb-sp/  # xtb singlepoint calculation results, based on xtb modredundant(fix) optimized results
            Xu01-1a-2a-major-xtbfix-sp.xyz  # input xyz file
            Xu01-1a-2a-major-xtbfix-sp.log  # log file
            Xu01-1a-2a-major-xtbfix-sp.charges  # charge file
            Xu01-1a-2a-major-xtbfix-sp.wbo  # wiberg bond order file
            ...
        
        xtb-mod-gau-sp/  # gaussian singlepoint calculation results, based on xtb modredundant(constrain) optimized results
            log/
                Xu01-1a-2a-major-xtbgausp.log
                Xu01-1a-2a-minor-xtbgausp.log
                Xu02-1a-2a-major-xtbgausp.log
                Xu02-1a-2a-minor-xtbgausp.log
                ...
            fchk/
                Xu01-1a-2a-major-xtbgausp.fchk
                Xu01-1a-2a-minor-xtbgausp.fchk
                Xu02-1a-2a-major-xtbgausp.fchk
                Xu02-1a-2a-minor-xtbgausp.fchk
                ...
            Xu01-1a-2a-major-xtbgausp.gjf  # calculation input file
            ...

        xtb-mod-gau-sp/  # gaussian singlepoint calculation results, based on xtb modredundant(fix) optimized results
            log/
                Xu01-1a-2a-major-xtbfixgausp.log
                Xu01-1a-2a-minor-xtbfixgausp.log
                Xu02-1a-2a-major-xtbfixgausp.log
                Xu02-1a-2a-minor-xtbfixgausp.log
                ...
            fchk/
                Xu01-1a-2a-major-xtbfixgausp.fchk
                Xu01-1a-2a-minor-xtbfixgausp.fchk
                Xu02-1a-2a-major-xtbfixgausp.fchk
                Xu02-1a-2a-minor-xtbfixgausp.fchk
                ...
            Xu01-1a-2a-major-xtbfixgausp.gjf  # calculation input file
            ...
```

## **Experimental data csv file structure**
```
complex,yield(%),ee(%),temp(C),time(h)
Xu01-1a-2a,33,2,25,72
Xu02-1a-2a,81,85,25,72
Xu03-1a-2a,68,86,25,72
...
```

## **Usage**

0. copy all raw files into rawmodel/ folder

1. activate ML conda environment (will output env.yml file later)

2. import Database class:  
```
from generator import *  
DB = DBgenerator()  # default rawmodel folder is rawmodel under current directory
```  

3. then you can run different commands to generate and calculate files, 
extract commands are also avaliable in this class