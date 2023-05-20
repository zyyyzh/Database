'''
Database generator for ZS-CMJ

Author: Zihao Ye

CreateDate: 2023-02-22
Version: 2023-03-05

Target:
1. read all raw structures from ZS-CMJ/rawmodel  

2. generate inp file of DFT-mod, xtb-mod, xtb-fixmod, gauxtb-mod based on model files or rules provided  
TODO: generate conformation search input file
TODO: add nocheck to all generator

3. submit(gau) or run(xtb) jobs  

Discriptor extractor:
Target:
0. all data should be ready according to `Database structure` by now  

1. read all raw structures from ZS-CMJ/rawmodel, generate class, which provides methods to get data needed  
TODO: read ee value, yield, reaction contiditions etc. from csv  
TODO: read from hdf5 and recreate class, which can add new data to  

2. extract data specified by user and add to tmp data  

3. generate hdf5 files and input data for pytorch at command 

Version v0.1 target:
mainly realize extract global data/feature  
output data into csv file  
'''

import os
import sys
import pandas as pd
from scripts.batchgjf import *
from scripts.runxtb import *
from scripts.extractor import *
from scripts.gaucheck import *

class DBgenerator:
    def __init__(self, rawmodel_dir='rawmodel/'):
        '''
        set up working directory, read models from rawmodel_dir

        rawmodel_dir: the directory of raw model structures
        '''
        self.rawmodel_dir = os.path.abspath(rawmodel_dir)  # /home/yzh/Database/ZS-CMJ/rawmodel
        assert os.path.exists(self.rawmodel_dir), 'rawmodel_dir not found!'
        self.db_dir = os.path.dirname(self.rawmodel_dir)  # /home/yzh/Database/ZS-CMJ
        self.data_dir = os.path.join(self.db_dir, 'data')  # /home/yzh/Database/ZS-CMJ/data

        self.model_list = [model.split('.')[0] for model in os.listdir(self.rawmodel_dir)]  # ['Xu01-1a-2a-major', 'Xu01-1a-2a-minor', ...]
        self.model_list.sort()  # sort model list
        self.data_dict = {'structure':self.model_list}
        self.db_size = len(self.model_list)  # model file number
        self.pair_db_size = self.db_size/2  # pair model file number, currently simply divide by 2
        # TODO: extract pair information from model name
        print('Database size: %d' % self.db_size)
        print('Paired database size: %d' % self.pair_db_size)

        self.generator_dict = {
            'DFT-mod': 0,  # 0: no dir, 1: dir exists, TODO: 2: all input files are generated, 3: all output files are generated
            'xtb-mod': 0,
            'xtb-fixmod': 0,
            'gauxtb-mod': 0,
            'DFT-mod-gau-sp': 0,
            'gauxtb-mod-gau-sp': 0,
            'xtb-mod-xtb-sp': 0,
            'xtb-fixmod-xtb-sp': 0,
            'xtb-mod-gau-sp': 0,
            'xtb-fixmod-gau-sp': 0,
            # 'conformation': 0,
        }

        # check current file status and update generator_dict
        self.check_all()

    # check status
    def _check_DFT_mod(self):
        '''
        check DFT-mod status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod')):
            self.generator_dict['DFT-mod'] = 0
            print('dir DFT-mod not found!')
            print('generate DFT-mod by running generate_DFT_mod()')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir DFT-mod found!')
            self.generator_dict['DFT-mod'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod', model+'-gau.gjf')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['DFT-mod'] = 2
            print('all DFT-mod input files found!')
        else:
            print('generate DFT-mod input files by running generate_DFT_mod()')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod/log', model+'-gau.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod/fchk', model+'-gau.fchk')):
                # print('fchk file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['DFT-mod'] = 3
            print('all DFT-mod output files found!')
        else:
            print('generate DFT-mod output file by running submit_DFT_mod() or submit gaussian jobs manually!')
            return out_list

    def _check_xtb_mod(self):
        '''
        check xtb-mod status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod')):
            self.generator_dict['xtb-mod'] = 0
            print('dir xtb-mod not found!')
            print('generate xtb-mod by running generate_xtb_mod()')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir xtb-mod found!')
            self.generator_dict['xtb-mod'] = 1

        inp_exist = 1
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod', 'constrain.inp')):
            print('constrain.inp not found!')
            inp_exist = 0
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod', model+'-xtb.xyz')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['xtb-mod'] = 2
            print('all xtb-mod input files found!')
        elif os.path.exists(os.path.join(self.db_dir, 'utils', 'constrain.inp')):
            print('generate xtb-mod input files by running generate_xtb_mod(), constrain.inp found!')
            return inp_list
        else:
            print('create constrain.inp first and generate xtb-mod input files by running generate_xtb_mod()')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod', model+'-xtb.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod', model+'-xtb-out.xyz')):
                # print('output xyz file for %s not found!' % model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod', model+'-xtb.charges')):
                # print('charge file for %s not found!' % model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod', model+'-xtb.wbo')):
                # print('wbo file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['xtb-mod'] = 3
            print('all xtb-mod output files found!')
        else:
            print('generate xtb-mod output file by running run_xtb_mod() or submit xtb jobs manually!')
            return out_list

    def _check_xtb_fixmod(self):
        '''
        check xtb-fixmod status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod')):
            self.generator_dict['xtb-fixmod'] = 0
            print('dir xtb-fixmod not found!')
            print('generate xtb-fixmod by running generate_xtb_fixmod()')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir xtb-fixmod found!')
            self.generator_dict['xtb-fixmod'] = 1

        inp_exist = 1
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod', 'fix.inp')):
            print('fix.inp not found!')
            inp_exist = 0
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod', model+'-xtbfix.xyz')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['xtb-fixmod'] = 2
            print('all xtb-fixmod input files found!')
        elif os.path.exists(os.path.join(self.db_dir, 'utils', 'fix.inp')):
            print('generate xtb-fixmod input files by running generate_xtb_fixmod(), fix.inp found!')
            return inp_list
        else:
            print('create fix.inp first and generate xtb-fixmod input files by running generate_xtb_fixmod()')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod', model+'-xtbfix.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod', model+'-xtbfix.charges')):
                # print('charge file for %s not found!' % model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod', model+'-xtbfix.wbo')):
                # print('wbo file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['xtb-fixmod'] = 3
            print('all xtb-fixmod output files found!')
        else:
            print('generate xtb-fixmod output file by running run_xtb_fixmod() or submit xtb jobs manually!')
            return out_list

    def _check_gauxtb_mod(self):
        '''
        check gauxtb-mod status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod')):
            self.generator_dict['gauxtb-mod'] = 0
            print('\ndir gauxtb-mod not found!\n')
            print('\ngenerate gauxtb-mod by running generate_gauxtb_mod()\n')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir gauxtb-mod found!')
            self.generator_dict['gauxtb-mod'] = 1

        inp_exist = 1
        for file in ['extderi', 'genxyz', 'xtb.sh']:
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod', file)):
                print(file, 'not found!')
                inp_exist = 0
                break

        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod', model+'-gauxtb.gjf')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['gauxtb-mod'] = 2
            print('\nall gauxtb-mod input files found!\n')
        else:
            print('\ngenerate gauxtb-mod input files by running generate_gauxtb_mod()\n')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod/log', model+'-gauxtb.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod/fchk', model+'-gauxtb.fchk')):
                # print('fchk file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['gauxtb-mod'] = 3
            print('\nall gauxtb-mod output files found!\n')
        else:
            print('\ngenerate gauxtb-mod output file by running submit_gauxtb_mod() or submit gaussian jobs manually!\n')
            return out_list

    def _check_DFT_mod_gau_sp(self):
        '''
        check DFT-mod-gau-sp status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod-gau-sp')):
            self.generator_dict['DFT-mod-gau-sp'] = 0
            print('\ndir DFT-mod-gau-sp not found!\n')
            print('\ngenerate DFT-mod-gau-sp by running generate_DFT_mod_gau_sp()\n')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir DFT-mod-gau-sp found!')
            self.generator_dict['DFT-mod-gau-sp'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod-gau-sp', model+'-gaugausp.gjf')):
                print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['DFT-mod-gau-sp'] = 2
            print('\nall DFT-mod-gau-sp input files found!\n')
        else:
            print('\ngenerate DFT-mod-gau-sp input files by running generate_DFT_mod_gau_sp()\n')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod-gau-sp/log', model+'-gaugausp.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'DFT-mod-gau-sp/fchk', model+'-gaugausp.fchk')):
                # print('fchk file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['DFT-mod-gau-sp'] = 3
            print('\nall dft-mod-gau-sp output files found!\n')
        else:
            print('\ngenerate dft-mod-gau-sp output file by running submit_dft_mod_gau_sp() or submit gaussian jobs manually!\n')
            return out_list

    def _check_gauxtb_mod_gau_sp(self):
        '''
        check gau-mod-gau-sp status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod-gau-sp')):
            self.generator_dict['gauxtb-mod-gau-sp'] = 0
            print('\ndir gauxtb-mod-gau-sp not found!\n')
            print('\ngenerate gauxtb-mod-gau-sp by running generate_gauxtb_mod_gau_sp()\n')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir gauxtb-mod-gau-sp found!')
            self.generator_dict['gauxtb-mod-gau-sp'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod-gau-sp', model+'-gauxtbgausp.gjf')):
                print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['gauxtb-mod-gau-sp'] = 2
            print('\nall gauxtb-mod-gau-sp input files found!\n')
        else:
            print('\ngenerate gauxtb-mod-gau-sp input files by running generate_gauxtb_mod_gau_sp()\n')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod-gau-sp/log', model+'-gauxtbgausp.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'gauxtb-mod-gau-sp/fchk', model+'-gauxtbgausp.fchk')):
                # print('fchk file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['gauxtb-mod-gau-sp'] = 3
            print('\nall gauxtb-mod-gau-sp output files found!\n')
        else:
            print('\ngenerate gauxtb-mod-gau-sp output file by running submit_gauxtb_mod_gau_sp() or submit gaussian jobs manually!\n')
            return out_list

    def _check_xtb_mod_xtb_sp(self):
        '''
        check xtb-mod-xtb-sp status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-xtb-sp')):
            self.generator_dict['xtb-mod-xtb-sp'] = 0
            print('dir xtb-mod-xtb-sp not found!')
            print('generate xtb-mod-xtb-sp by running generate_xtb_mod_xtb_sp()')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir xtb-mod-xtb-sp found!')
            self.generator_dict['xtb-mod-xtb-sp'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-xtb-sp', model+'-xtb-sp.xyz')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['xtb-mod-xtb-sp'] = 2
            print('all xtb-mod-xtb-sp input files found!')
        else:
            print('generate xtb-mod-xtb-sp input files by running generate_xtb_mod_xtb_sp()')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-xtb-sp', model+'-xtb-sp.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-xtb-sp', model+'-xtb-sp.charges')):
                # print('charge file for %s not found!' % model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-xtb-sp', model+'-xtb-sp.wbo')):
                # print('wbo file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['xtb-mod-xtb-sp'] = 3
            print('all xtb-mod-xtb-sp output files found!')
        else:
            print('generate xtb-mod-xtb-sp output file by running run_xtb_mod_xtb_sp() or submit xtb jobs manually!')
            return out_list

    def _check_xtb_fixmod_xtb_sp(self):
        '''
        check xtb-fixmod-xtb-sp status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-xtb-sp')):
            self.generator_dict['xtb-fixmod-xtb-sp'] = 0
            print('dir xtb-fixmod-xtb-sp not found!')
            print('generate xtb-fixmod-xtb-sp by running generate_xtb_fixmod_xtb_sp()')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir xtb-fixmod-xtb-sp found!')
            self.generator_dict['xtb-fixmod-xtb-sp'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-xtb-sp', model+'-xtbfix-sp.xyz')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['xtb-fixmod-xtb-sp'] = 2
            print('all xtb-fixmod-xtb-sp input files found!')
        else:
            print('generate xtb-fixmod-xtb-sp input files by running generate_xtb_fixmod_xtb_sp()')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-xtb-sp', model+'-xtbfix-sp.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-xtb-sp', model+'-xtbfix-sp.charges')):
                # print('charge file for %s not found!' % model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-xtb-sp', model+'-xtbfix-sp.wbo')):
                # print('wbo file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['xtb-fixmod-xtb-sp'] = 3
            print('all xtb-fixmod-xtb-sp output files found!')
        else:
            print('generate xtb-fixmod-xtb-sp output file by running run_xtb_fixmod_xtb_sp() or submit xtb jobs manually!')
            return out_list 

    def _check_xtb_mod_gau_sp(self):
        '''
        check xtb-mod-gau-sp status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-gau-sp')):
            self.generator_dict['xtb-mod-gau-sp'] = 0
            print('\ndir xtb-mod-gau-sp not found!\n')
            print('\ngenerate xtb-mod-gau-sp by running generate_xtb_mod_gau_sp()\n')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir xtb-mod-gau-sp found!')
            self.generator_dict['xtb-mod-gau-sp'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-gau-sp', model+'-xtbgausp.gjf')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['xtb-mod-gau-sp'] = 2
            print('\nall xtb-mod-gau-sp input files found!\n')
        else:
            print('\ngenerate xtb-mod-gau-sp input files by running generate_xtb_mod_gau_sp()\n')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-gau-sp/log', model+'-xtbgausp.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-mod-gau-sp/fchk', model+'-xtbgausp.fchk')):
                # print('fchk file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['xtb-mod-gau-sp'] = 3
            print('\nall xtb-mod-gau-sp output files found!\n')
        else:
            print('\ngenerate xtb-mod-gau-sp output file by running submit_xtb_mod_gau_sp() or submit gaussian jobs manually!\n')
            return out_list

    def _check_xtb_fixmod_gau_sp(self):
        '''
        check xtb-fixmod-gau-sp status
        update self.generator_dict
        output status and provide choice
        '''
        inp_list = []
        if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-gau-sp')):
            self.generator_dict['xtb-fixmod-gau-sp'] = 0
            print('\ndir xtb-fixmod-gau-sp not found!\n')
            print('\ngenerate xtb-fixmod-gau-sp by running generate_xtb_fixmod_gau_sp()\n')
            inp_list = self.model_list
            return inp_list
        else:
            print('dir xtb-fixmod-gau-sp found!')
            self.generator_dict['xtb-fixmod-gau-sp'] = 1

        inp_exist = 1
        for model in self.model_list:  # check input file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-gau-sp', model+'-xtbfixgausp.gjf')):
                # print('input file for %s not found!' % model)
                inp_list.append(model)
                inp_exist = 0
        if inp_exist:  # all input files exist
            self.generator_dict['xtb-fixmod-gau-sp'] = 2
            print('\nall xtb-fixmod-gau-sp input files found!\n')
        else:
            print('\ngenerate xtb-fixmod-gau-sp input files by running generate_xtb_fixmod_gau_sp()\n')
            return inp_list
            
        out_exist = 1
        out_list = []
        for model in self.model_list:  # check output file
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-gau-sp/log', model+'-xtbfixgausp.log')):
                # print('log file for %s not found!' % model)
                out_list.append(model)
                out_exist = 0
            if not os.path.exists(os.path.join(self.db_dir, 'xtb-fixmod-gau-sp/fchk', model+'-xtbfixgausp.fchk')):
                # print('fchk file for %s not found!' % model)
                out_exist = 0
        if out_exist:  # all output files exist
            self.generator_dict['xtb-fixmod-gau-sp'] = 3
            print('\nall xtb-fixmod-gau-sp output files found!\n')
        else:
            print('\ngenerate xtb-fixmod-gau-sp output file by running submit_xtb_fixmod_gau_sp() or submit gaussian jobs manually!\n')
            return out_list
        
    def check_all(self):
        '''
        check all file status in database
        '''
        self._check_DFT_mod()
        self._check_xtb_mod()
        self._check_xtb_fixmod()
        self._check_gauxtb_mod()
        self._check_DFT_mod_gau_sp()
        self._check_gauxtb_mod_gau_sp()
        self._check_xtb_mod_xtb_sp()
        self._check_xtb_fixmod_xtb_sp()
        self._check_xtb_mod_gau_sp()
        self._check_xtb_fixmod_gau_sp()

        print(self.generator_dict)

    def check_gau_files(self, dir_name):
        '''
        check if gaussian jobs terminate normally
        '''
        self.check_all()
        assert dir_name in ['DFT-mod', 'gauxtb-mod', 'DFT-mod-gau-sp', 'gauxtb-mod-gau-sp', 'xtb-mod-gau-sp', 'xtb-fixmod-gau-sp'], 'dir name should be DFT-mod, gauxtb-mod, gauxtb-mod-gau-sp, xtb-mod-gau-sp or xtb-fixmod-gau-sp'
        assert self.generator_dict[dir_name] == 3, 'generate and process output files first'
        
        gau_check_result = gaucheck(os.path.join(self.db_dir, dir_name, 'log'))

        if type(gau_check_result) is str:
            print(dir_name, gau_check_result)
        elif type(gau_check_result) is list:
            print(dir_name, 'abnormal files:')
            for f in gau_check_result:
                print(f)

    # generate input files
    def generate_DFT_mod(self, no_check=False):
        '''
        generate DFT-mod based on rawmodel
        '''
        inp_list = self._check_DFT_mod()
        if self.generator_dict['DFT-mod'] >= 2 and not no_check:
            print('DFT-mod files already done!')
            return
        else:
            raw_gjf_list = list(map(lambda x: self.rawmodel_dir + '/' + x + '.gjf', inp_list))
            model_gjf_path = self.db_dir + '/utils/gaumodel.gjf'
            target_path = self.db_dir + '/DFT-mod'
            if not os.path.exists(target_path):
                os.mkdir(target_path)
            for raw_gjf in raw_gjf_list:
                raw_name = os.path.basename(raw_gjf).split('.')[0]
                ofile_name = target_path + '/' + raw_name + '-gau'
                from_gjf_to_gjf(raw_gjf, model_gjf_path, ofile_name)
                print('gaussian input file generated: ', ofile_name + '.gjf')

    def generate_xtb_mod(self, no_check=False):
        '''
        generate xtb-mod based on rawmodel
        '''
        inp_list = self._check_xtb_mod()
        if self.generator_dict['xtb-mod'] >= 2 and not no_check:
            print('xtb-mod files already done!')
            return
        else:
            raw_gjf_list = list(map(lambda x: self.rawmodel_dir + '/' + x + '.gjf', inp_list))
            target_path = self.db_dir + '/xtb-mod'
            if not os.path.exists(target_path):
                os.mkdir(target_path)
            for raw_gjf in raw_gjf_list:
                raw_name = os.path.basename(raw_gjf).split('.')[0]
                ofile_name = target_path + '/' + raw_name + '-xtb'
                from_gjf_to_xyz(raw_gjf, ofile_name)
                print('xtb input xyz file generated: ', ofile_name + '.xyz')
            
            os.system('cp ' + self.db_dir + '/utils/constrain.inp ' + self.db_dir + '/xtb-mod/')

    def generate_xtb_fixmod(self, no_check=False):
        '''
        generate xtb-fixmod based on rawmodel
        '''
        inp_list = self._check_xtb_fixmod()
        if self.generator_dict['xtb-fixmod'] >= 2 and not no_check:
            print('xtb-fixmod files already done!')
            return
        else:
            raw_gjf_list = list(map(lambda x: self.rawmodel_dir + '/' + x + '.gjf', inp_list))
            target_path = self.db_dir + '/xtb-fixmod'
            if not os.path.exists(target_path):
                os.mkdir(target_path)
            for raw_gjf in raw_gjf_list:
                raw_name = os.path.basename(raw_gjf).split('.')[0]
                ofile_name = target_path + '/' + raw_name + '-xtbfix'
                from_gjf_to_xyz(raw_gjf, ofile_name)
                print('xtb input xyz file generated: ', ofile_name + '.xyz')

            os.system('cp ' + self.db_dir + '/utils/fix.inp ' + self.db_dir + '/xtb-fixmod/')

    def generate_gauxtb_mod(self, no_check=False):
        '''
        generate gauxtb-mod based on rawmodel
        '''
        inp_list = self._check_gauxtb_mod()
        if self.generator_dict['gauxtb-mod'] >= 2 and not no_check:
            print('gauxtb-mod files already done!')
            return
        else:
            os.system('cp ' + self.db_dir + '/utils/extderi ' + self.db_dir + '/gauxtb-mod/')
            os.system('cp ' + self.db_dir + '/utils/genxyz ' + self.db_dir + '/gauxtb-mod/')
            os.system('cp ' + self.db_dir + '/utils/xtb.sh ' + self.db_dir + '/gauxtb-mod/')
            raw_gjf_list = list(map(lambda x: self.rawmodel_dir + '/' + x + '.gjf', inp_list))
            model_gjf_path = self.db_dir + '/utils/gauxtbmodel.gjf'
            target_path = self.db_dir + '/gauxtb-mod'
            if not os.path.exists(target_path):
                os.mkdir(target_path)
            for raw_gjf in raw_gjf_list:
                raw_name = os.path.basename(raw_gjf).split('.')[0]
                ofile_name = target_path + '/' + raw_name + '-gauxtb'
                from_gjf_to_gjf(raw_gjf, model_gjf_path, ofile_name)
                print('gaussian-xtb input file generated: ', ofile_name + '.gjf')

    def generate_DFT_mod_gau_sp(self, no_check=False):
        '''
        generate gauxtb-mod-gau-sp based on rawmodel
        '''
        self._check_DFT_mod()
        inp_list = self._check_DFT_mod_gau_sp()
        if self.generator_dict['DFT-mod'] < 3 and not no_check:
            print('DFT-mod calculations not done yet!')
            return
        else:
            if self.generator_dict['DFT-mod-gau-sp'] >= 2 and not no_check:
                print('DFT-mod-gau-sp files already done!')
                return
            else:
                raw_log_list = list(map(lambda x: self.db_dir + '/DFT-mod/log/' + x + '-gau.log', inp_list))
                model_gjf_path = self.db_dir + '/utils/gauspmodel.gjf'
                target_path = self.db_dir + '/DFT-mod-gau-sp'
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
                for raw_log in raw_log_list:
                    raw_name = os.path.basename(raw_log).split('.')[0]
                    ofile_name = target_path + '/' + raw_name + 'gausp'
                    from_log_to_gjf(raw_log, model_gjf_path, ofile_name)
                    print('DFT-mod-gau-sp input file generated: ', ofile_name + '.gjf')

    def generate_gauxtb_mod_gau_sp(self, no_check=False):
        '''
        generate gauxtb-mod-gau-sp based on rawmodel
        '''
        self._check_gauxtb_mod()
        inp_list = self._check_gauxtb_mod_gau_sp()
        if self.generator_dict['gauxtb-mod'] < 3 and not no_check:
            print('gauxtb-mod calculations not done yet!')
            return
        else:
            if self.generator_dict['gauxtb-mod-gau-sp'] >= 2 and not no_check:
                print('gauxtb-mod-gau-sp files already done!')
                return
            else:
                raw_log_list = list(map(lambda x: self.db_dir + '/gauxtb-mod/log/' + x + '-gauxtb.log', inp_list))
                model_gjf_path = self.db_dir + '/utils/gauspmodel.gjf'
                target_path = self.db_dir + '/gauxtb-mod-gau-sp'
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
                for raw_log in raw_log_list:
                    raw_name = os.path.basename(raw_log).split('.')[0]
                    ofile_name = target_path + '/' + raw_name + 'gausp'
                    from_log_to_gjf(raw_log, model_gjf_path, ofile_name)
                    print('gauxtb-mod-gau-sp input file generated: ', ofile_name + '.gjf')

    def generate_xtb_mod_xtb_sp(self, no_check=False):
        '''
        generate xtb-mod-xtb-sp based on xtb-mod
        '''
        self._check_xtb_mod()
        inp_list = self._check_xtb_mod_xtb_sp()
        if self.generator_dict['xtb-mod'] < 3 and not no_check:
            print('xtb-mod calculations not done yet!')
            return
        else:
            if self.generator_dict['xtb-mod-xtb-sp'] >= 2 and not no_check:
                print('xtb-mod-xtb-sp files already done!')
                return
            else:
                raw_xyz_list = list(map(lambda x: self.db_dir + '/xtb-mod/' + x + '-xtb-out.xyz', inp_list))
                target_path = self.db_dir + '/xtb-mod-xtb-sp'
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
                for raw_xyz in raw_xyz_list:
                    raw_name = os.path.basename(raw_xyz).split('.')[0]
                    ofile_name = target_path + '/' + raw_name[:-8] + '-xtb-sp'
                    os.system('cp ' + raw_xyz + ' ' + ofile_name + '.xyz')
                    print('xtb sp input xyz file generated: ', ofile_name + '.xyz')

    def generate_xtb_fixmod_xtb_sp(self, no_check=False):
        '''
        generate xtb-fixmod-xtb-sp based on xtb-fixmod
        '''
        self._check_xtb_fixmod()
        inp_list = self._check_xtb_fixmod_xtb_sp()
        if self.generator_dict['xtb-fixmod'] < 3 and not no_check:
            print('xtb-fixmod calculations not done yet!')
            return
        else:
            if self.generator_dict['xtb-fixmod-xtb-sp'] >= 2 and not no_check:
                print('xtb-fixmod-xtb-sp files already done!')
                return
            else:
                raw_xyz_list = list(map(lambda x: self.db_dir + '/xtb-fixmod/' + x + '-xtbfix-out.xyz', inp_list))
                target_path = self.db_dir + '/xtb-fixmod-xtb-sp'
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
                for raw_xyz in raw_xyz_list:
                    raw_name = os.path.basename(raw_xyz).split('.')[0]
                    ofile_name = target_path + '/' + raw_name[:-11] + '-xtbfix-sp'
                    os.system('cp ' + raw_xyz + ' ' + ofile_name + '.xyz')
                    print('xtb sp input xyz file generated: ', ofile_name + '.xyz')

    def generate_xtb_mod_gau_sp(self, no_check=False):
        '''
        generate xtb-mod-gau-sp based on xtb-mod output xyz
        '''
        self._check_xtb_mod()
        inp_list = self._check_xtb_mod_gau_sp()
        if self.generator_dict['xtb-mod'] < 3 and not no_check:
            print('xtb-mod calculations not done yet!')
            return
        else:
            if self.generator_dict['xtb-mod-gau-sp'] >= 2 and not no_check:
                print('xtb-mod-gau-sp files already done!')
                return
            else:
                raw_xyz_list = list(map(lambda x: self.db_dir + '/xtb-mod/' + x + '-xtb-out.xyz', inp_list))
                model_gjf_path = self.db_dir + '/utils/gauspmodel.gjf'
                target_path = self.db_dir + '/xtb-mod-gau-sp'
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
                for raw_xyz in raw_xyz_list:
                    raw_name = os.path.basename(raw_xyz).split('.')[0]
                    ofile_name = target_path + '/' + raw_name[:-4] + 'gausp'
                    from_xyz_to_gjf(raw_xyz, model_gjf_path, ofile_name)
                    print('xtb-mod-gau-sp input file generated: ', ofile_name + '.gjf')

    def generate_xtb_fixmod_gau_sp(self, no_check=False):
        '''
        generate xtb-fixmod-gau-sp based on xtb-fixmod output xyz
        '''
        self._check_xtb_fixmod()
        inp_list = self._check_xtb_fixmod_gau_sp()
        if self.generator_dict['xtb-fixmod'] < 3 and not no_check:
            print('xtb-fixmod calculations not done yet!')
            return
        else:
            if self.generator_dict['xtb-fixmod-gau-sp'] >= 2 and not no_check:
                print('xtb-fixmod-gau-sp files already done!')
                return
            else:
                raw_xyz_list = list(map(lambda x: self.db_dir + '/xtb-fixmod/' + x + '-xtbfix-out.xyz', inp_list))
                model_gjf_path = self.db_dir + '/utils/gauspmodel.gjf'
                target_path = self.db_dir + '/xtb-fixmod-gau-sp'
                if not os.path.exists(target_path):
                    os.mkdir(target_path)
                for raw_xyz in raw_xyz_list:
                    raw_name = os.path.basename(raw_xyz).split('.')[0]
                    ofile_name = target_path + '/' + raw_name[:-4] + 'gausp'
                    from_xyz_to_gjf(raw_xyz, model_gjf_path, ofile_name)
                    print('xtb-fixmod-gau-sp input file generated: ', ofile_name + '.gjf')

    def generate_conformation(self):  # not ready
        '''
        generate conformation search input file
        '''
        pass

    def generate_all_xtb(self):
        '''
        generate and run all xtb calculation files in database
        '''
        self.generate_xtb_mod()
        self.generate_xtb_fixmod()
        self.run_xtb_mod()
        self.run_xtb_fixmod()
        self.generate_xtb_mod_xtb_sp()
        self.generate_xtb_fixmod_xtb_sp()
        self.run_xtb_mod_xtb_sp()
        self.run_xtb_fixmod_xtb_sp()

        self.check_all()

    def generate_all_first_step(self):
        '''
        generate and run all first step calculation files in database
        '''
        self.generate_DFT_mod()
        self.generate_gauxtb_mod()
        self.generate_xtb_mod()
        self.generate_xtb_fixmod()

        self.check_all()

    def generate_all_sp_step(self):  # not ready
        pass

    # run xtb calculation directly
    def run_xtb_mod(self):
        '''
        run xtb-mod
        '''
        out_list = self._check_xtb_mod()
        if self.generator_dict['xtb-mod'] < 2:
            print('generate xtb-mod files first!')
            return
        elif self.generator_dict['xtb-mod'] == 2:
            target_path = self.db_dir + '/xtb-mod'
            for model in out_list:
                file = model + '-xtb.xyz'
                submit_xtb_job(target_path + '/' + file, inp_name=target_path + '/constrain.inp', job_type='opt')
        elif self.generator_dict['xtb-mod'] == 3:
            print('xtb-mod calculations already done!')
            return

    def run_xtb_fixmod(self):
        '''
        run xtb-fixmod
        '''
        out_list = self._check_xtb_fixmod()
        if self.generator_dict['xtb-fixmod'] < 2:
            print('generate xtb-fixmod files first!')
            return
        elif self.generator_dict['xtb-fixmod'] == 2:
            target_path = self.db_dir + '/xtb-fixmod'
            for model in out_list:
                file = model + '-xtbfix.xyz'
                submit_xtb_job(target_path + '/' + file, inp_name=target_path + '/fix.inp', job_type='opt')
        elif self.generator_dict['xtb-fixmod'] == 3:
            print('xtb-fixmod calculations already done!')
            return
        
    def run_xtb_mod_xtb_sp(self):
        '''
        run xtb-mod-stb-sp
        '''
        out_list = self._check_xtb_mod_xtb_sp()
        if self.generator_dict['xtb-mod-xtb-sp'] < 2:
            print('generate xtb-mod-xtb-sp files first!')
            return
        elif self.generator_dict['xtb-mod-xtb-sp'] == 2:
            target_path = self.db_dir + '/xtb-mod-xtb-sp'
            for model in out_list:
                file = model + '-xtb-sp.xyz'
                submit_xtb_job(target_path + '/' + file, job_type='sp')
        elif self.generator_dict['xtb-mod-xtb-sp'] == 3:
            print('xtb-mod-xtb-sp calculations already done!')
            return

    def run_xtb_fixmod_xtb_sp(self):
        '''
        run xtb-fixmod-stb-sp
        '''
        out_list = self._check_xtb_fixmod_xtb_sp()
        if self.generator_dict['xtb-fixmod-xtb-sp'] < 2:
            print('generate xtb-fixmod-xtb-sp files first!')
            return
        elif self.generator_dict['xtb-fixmod-xtb-sp'] == 2:
            target_path = self.db_dir + '/xtb-fixmod-xtb-sp'
            for model in out_list:
                file = model + '-xtbfix-sp.xyz'
                submit_xtb_job(target_path + '/' + file, job_type='sp')
        elif self.generator_dict['xtb-fixmod-xtb-sp'] == 3:
            print('xtb-fixmod-xtb-sp calculations already done!')
            return

    # submit g09 calculation to SGE
    def submit_DFT_mod(self):
        '''
        submit DFT-mod calculation
        '''
        self.check_all()
        self._check_DFT_mod()
        if self.generator_dict['DFT-mod'] < 2:
            print('generate DFT-mod files first!')
            return
        elif self.generator_dict['DFT-mod'] == 2:
            os.chdir('DFT-mod')
            os.system('qg09 -p 8 -a')  # submit g09xtb calculation using qg09 script, proc=8
            os.chdir(self.db_dir)
        elif self.generator_dict['DFT-mod'] == 3:
            print('DFT-mod calculations already done!')
            return

    def submit_gauxtb_mod(self):
        '''
        submit gauxtb-mod calculation
        '''
        self.check_all()
        self._check_gauxtb_mod()
        if self.generator_dict['gauxtb-mod'] < 2:
            print('generate gauxtb-mod files first!')
            return
        elif self.generator_dict['gauxtb-mod'] == 2:
            os.chdir('gauxtb-mod')
            os.system('qg09 -p 1 -x -a')  # submit g09xtb calculation using qg09 script, proc=1
            os.chdir(self.db_dir)
        elif self.generator_dict['gauxtb-mod'] == 3:
            print('gauxtb-mod calculations already done!')
            return

    def submit_gau_sp(self, dir_name):
        '''
        submit gau-sp calculation
        '''
        self.check_all()
        assert dir_name in ['DFT-mod-gau-sp', 'gauxtb-mod-gau-sp', 'xtb-mod-gau-sp', 'xtb-fixmod-gau-sp'], 'dir name should be gauxtb-mod-gau-sp, xtb-mod-gau-sp or xtb-fixmod-gau-sp'
        if self.generator_dict[dir_name] < 2:
            print('generate {} files first!'.format(dir_name))
            return
        elif self.generator_dict[dir_name] == 2:
            os.chdir(dir_name)
            os.system('qg09 -p 8 -a')
            os.chdir(self.db_dir)
        elif self.generator_dict[dir_name] == 3:
            print('{} calculations already done!'.format(dir_name))
            return

    # process g09 calculation results
    def process_gau_result(self, dir_name):
        '''
        process gau result
        '''
        assert dir_name in ['DFT-mod', 'DFT-mod-gau-sp', 'gauxtb-mod', 'gauxtb-mod-gau-sp', 'xtb-mod-gau-sp', 'xtb-fixmod-gau-sp'], 'dir name should be gauxtb-mod-gau-sp, xtb-mod-gau-sp or xtb-fixmod-gau-sp'
        if self.generator_dict[dir_name] < 2:
            print('{} input file not ready!'.format(dir_name))
            return
        elif self.generator_dict[dir_name] == 3:
            print('{} calculations already done!'.format(dir_name))
            return
        elif self.generator_dict[dir_name] == 2:
            os.chdir(dir_name)
            os.makedirs('log', exist_ok=True)
            os.makedirs('fchk', exist_ok=True)
            for dir in os.listdir():
                if dir.isdigit():
                    os.system('cp {}/*.log log/'.format(dir))
                    os.system('cp {}/*.fchk fchk/'.format(dir))
                    os.system('rm -rf ' + dir)
            os.chdir(self.db_dir)
        
    # extract descriptor from xtb calculation results
    def extract_xtb_result(self, dir_list=None, discriptor_list=None, atom_list=None):
        '''
        extract xtb result according to discritor_list
        '''
        # define avaliable dir and discriptor
        avaliable_dir_list = ['xtb-mod', 'xtb-fixmod', 'xtb-mod-xtb-sp', 'xtb-fixmod-xtb-sp']
        avaliable_discriptor_list = ['SPE', 'Grad', 'Gap', 'ELUMO', 'EHOMO', 'charge']
        # parse dir input
        if dir_list is None:
            dir_list = avaliable_dir_list
        else:
            for dir in dir_list:
                assert dir in avaliable_dir_list, 'dir should be xtb-mod, xtb-fixmod, xtb-mod-xtb-sp or xtb-fixmod-xtb-sp'
        # parse discriptor input
        if discriptor_list is None:
            discriptor_list = avaliable_discriptor_list
        else:
            for discriptor in discriptor_list:
                assert discriptor in avaliable_discriptor_list, 'discriptor should be SPE, Grad, Gap, ELUMO, EHOMO or charge+atomidx'
        # parse atom input
        if atom_list is None:
            atom_list = []

        for dir in dir_list:
            for discriptor in discriptor_list:
                if discriptor == 'charge':
                    chrg_file_list = [file for file in os.listdir(self.db_dir + '/' + dir) if file.endswith('.charges')]
                    chrg_file_list.sort()
                    for atom in atom_list:
                        data_name = dir + '_' + discriptor + '-' + atom
                        data_list = []
                        for chrg_file in chrg_file_list:
                            data = extract_xtb_charge(self.db_dir + '/' + dir + '/' + chrg_file, int(atom))
                            data_list.append(data)
                        
                        self.data_dict[data_name] = data_list
                    continue

                data_name = dir + '_' + discriptor
                data_list = []
                log_file_list = [file for file in os.listdir(self.db_dir + '/' + dir) if file.endswith('.log')]
                log_file_list.sort()
                for log_file in log_file_list:
                    if discriptor == 'SPE':
                        data = extract_xtb_SPE(self.db_dir + '/' + dir + '/' + log_file)
                    elif discriptor == 'Grad':
                        data = extract_xtb_Grad(self.db_dir + '/' + dir + '/' + log_file)
                    elif discriptor == 'Gap':
                        data = extract_xtb_Gap(self.db_dir + '/' + dir + '/' + log_file)
                    elif discriptor == 'ELUMO':
                        data = extract_xtb_ELUMO(self.db_dir + '/' + dir + '/' + log_file)
                    elif discriptor == 'EHOMO':
                        data = extract_xtb_EHOMO(self.db_dir + '/' + dir + '/' + log_file)
                    data_list.append(data)

                self.data_dict[data_name] = data_list

    def extract_gaussian_result(self, dir_list=None, discriptor_list=None, atom_list=None):
        '''
        extract xtb result according to discritor_list
        '''
        # define avaliable dir and discriptor
        avaliable_dir_list = ['DFT-mod', 'DFT-mod-gau-sp', 'gauxtb-mod', 'gauxtb-mod-gau-sp', 'xtb-fixmod-gau-sp', 'xtb-mod-gau-sp']
        avaliable_discriptor_list = ['SPE', 'ForceRMS', 'ForceMax', 'G', 'EHOMO', 'ELUMO', 'Gap', 'charge']
        # parse dir input
        if dir_list is None:
            dir_list = avaliable_dir_list
        else:
            for dir in dir_list:
                assert dir in avaliable_dir_list, 'dir should be DFT-mod, DFT-mod-gau-sp, gauxtb-mod, gauxtb-mod-gau-sp, xtb-fixmod-gau-sp, xtb-mod-gau-sp'
        # parse discriptor input
        if discriptor_list is None:
            discriptor_list = avaliable_discriptor_list
        else:
            for discriptor in discriptor_list:
                assert discriptor in avaliable_discriptor_list, 'discriptor should be SPE, ForceRMS, ForceMax, EHOMO, ELUMO, Gap, G or charge+atomidx'
        # parse atom input
        if atom_list is None:
            atom_list = []

        for dir in dir_list:
            for discriptor in discriptor_list:
                if discriptor == 'charge':
                    chrg_file_list = [file for file in os.listdir(self.db_dir + '/' + dir + '/log') if file.endswith('.log')]
                    chrg_file_list.sort()
                    for atom in atom_list:
                        data_name = dir + '_' + discriptor + '-' + atom
                        data_list = []
                        for chrg_file in chrg_file_list:
                            data = extract_gau_Charge(self.db_dir + '/' + dir + '/log/' + chrg_file, int(atom))
                            data_list.append(data)
                        
                        self.data_dict[data_name] = data_list
                    continue

                if discriptor in ['EHOMO', 'ELUMO', 'Gap']:
                    data_name = dir + '_' + discriptor
                    data_list = []
                    fchk_file_list = [file for file in os.listdir(self.db_dir + '/' + dir + '/fchk') if file.endswith('.fchk')]
                    fchk_file_list.sort()
                    for fchk_file in fchk_file_list:
                        mo = extract_gau_MO(self.db_dir + '/' + dir + '/fchk/' + fchk_file)
                        if discriptor == 'EHOMO':
                            data = mo[0]
                        elif discriptor == 'ELUMO':
                            data = mo[1]
                        elif discriptor == 'Gap':
                            data = mo[2]
                        data_list.append(data)
                    
                    self.data_dict[data_name] = data_list
                    continue

                data_name = dir + '_' + discriptor
                data_list = []
                log_file_list = [file for file in os.listdir(self.db_dir + '/' + dir + '/log') if file.endswith('.log')]
                log_file_list.sort()
                for log_file in log_file_list:
                    free = extract_gau_Free_Energy(self.db_dir + '/' + dir + '/log/' + log_file)
                    force = extract_gau_Force(self.db_dir + '/' + dir + '/log/' + log_file)
                    if discriptor == 'SPE':
                        data = extract_gau_SPE(self.db_dir + '/' + dir + '/log/' + log_file)
                    elif discriptor == 'G':
                        data = free[1]
                    elif discriptor == 'ForceRMS':
                        data = force[0]
                    elif discriptor == 'ForceMax':
                        data = force[1]
                    data_list.append(data)

                self.data_dict[data_name] = data_list

    # output data_dict as csv file
    def output_original_data_csv(self, out_file=None):
        '''
        output data_dict as csv file
        '''
        data_df = pd.DataFrame(self.data_dict)
        if out_file is None:
            out_csv = os.path.join(self.data_dir, 'data.csv')
            data_df.to_csv(out_csv, index=False)
        else:
            data_df.to_csv(out_file, index=False)

    def output_pair_data_csv(self, out_file=None):
        '''
        output paired data as csv file
        xxx-major and xxx-minor is considered as a pair
        '''
        # create self.pair_data_dict, rename title names to xxx_major xxx_minor xxx_diff
        self.pair_data_dict = {}
        for title in self.data_dict.keys():
            if title == 'structure':
                self.pair_data_dict[title] = []
            else:
                self.pair_data_dict[title+'_major'] = []
                self.pair_data_dict[title+'_minor'] = []
                self.pair_data_dict[title+'_diff'] = []

        for i in range(int(self.pair_db_size)):
            major_idx = int(2*i)
            minor_idx = int(2*i+1)
            for title in self.data_dict.keys():
                if title == 'structure':
                    assert self.data_dict['structure'][major_idx][:-6] == self.data_dict['structure'][minor_idx][:-6], 'pair assign maybe wrong, please check'
                    self.pair_data_dict['structure'].append(self.data_dict['structure'][major_idx][:-6])
                else:
                    self.pair_data_dict[title+'_major'].append(self.data_dict[title][major_idx])
                    self.pair_data_dict[title+'_minor'].append(self.data_dict[title][minor_idx])
                    diff_data = float(self.data_dict[title][major_idx]) - float(self.data_dict[title][minor_idx])
                    self.pair_data_dict[title+'_diff'].append(format(diff_data, '.6f'))
        
        pair_data_df = pd.DataFrame(self.pair_data_dict)
        if out_file is None:
            out_csv = os.path.join(self.data_dir, 'pair_data.csv')
            pair_data_df.to_csv(out_csv, index=False)
        else:
            pair_data_df.to_csv(out_file, index=False)
   

if __name__ == '__main__':
    dbzs = DBgenerator()