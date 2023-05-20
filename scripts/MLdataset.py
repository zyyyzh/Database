'''
Pytroch Dataset used for read and filter csv files output by generater
Author: Zihao Ye
Date: 04-27-2023
'''

import math
import random
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
import statsmodels.api as sm


def ee_2_deltaG(ee_value, temp=298.15):
    '''
    convert ee% to free energy difference
    eevalue has unit of %
    temp is in K
    '''
    factor = 0.0019872

    ee_value = float(ee_value) * 0.01

    s_percent = (1+ee_value)/2  # S-product percentage
    r_percent = 1-s_percent  # R-product percentage

    r_q = r_percent/s_percent  # Q of R-product

    delta_G = -temp*factor*math.log(r_q)  # delta G

    return delta_G

def t_value_test(para_list, target_list, threshold=0.05):
    '''
    check whether para_list has significance effect on target_list
    threshold: pvalue <= threshold, return 1, else, return 0
    '''
    # prepare data
    y = np.array(target_list, dtype=float)
    x = np.array(para_list, dtype=float)
    x = sm.add_constant(x)

    # fit model and get p value
    model = sm.OLS(y,x)
    results = model.fit()
    pvalue = abs(results.t_test([0,1]).pvalue)

    return pvalue <= threshold


class PairDataset(Dataset):
    """
    expdata_file 是标签, 即实验ee%信息 data/expdata.csv
    pairdata_file 是参数, 即计算所得major-minor pair信息 data/pair_data.csv
    
    可使用filters进行筛选, 默认均为空列表, 即无筛选, 输入参数为删去
    calc_type_filter(list): 获得数据的计算方法, 如DFT-mod
    major_minor_filter(list): 有major, minor, diff三个选项
    parameter_filter(list): 根据计算得到的参数类型决定, 如SPE
    t_test_filter(bool): 是否进行t_test检验, 若是, 则删去t_test不通过的参数
    deltaG(bool): 是否将ee%输入转换为ΔG, 默认为False
    percent(bool): 是否将ee%输入换算为小数, 默认为False
    output_new_csv(bool): 是否将处理后的数据输出到新的csv文件中, 默认为False
    structure_filter(list): 筛选complex structure, 如Xu08-1a-2a
    """
    def __init__(self, expdata_file, pair_data_file,
                 calc_type_filter=[],
                 major_minor_filter=[],
                 parameter_filter=[],
                 t_test_filter=False,
                 deltaG=False,
                 percent=False,
                 output_new_csv=False,
                 structure_filter=[],
                 ):
        
        # read expdata and modify
        self.expdata_df = pd.read_csv(expdata_file, index_col=0).sort_index()  # read experimental results to a dataframe
        self.structure_filter = structure_filter
        # apply structure filter
        if self.structure_filter != []:
            self.expdata_df = self.expdata_df.drop(self.structure_filter)
        self.expdata_enantio_df = self.expdata_df['ee(%)']  # extract ee value to a list
        self.deltaG = deltaG
        self.percent = percent
        if self.deltaG:  # convert ee% to delta G
            assert self.percent == False, 'cannot set deltaG and percent True at the same time!'
            self.expdata_enantio_df = self.expdata_enantio_df.apply(ee_2_deltaG)
        if self.percent:  # divide ee% value by 100
            assert self.deltaG == False, 'cannot set deltaG and percent True at the same time!'
            self.expdata_enantio_df = self.expdata_enantio_df / 100

        # read calculation data
        self.full_pair_data_df = pd.read_csv(pair_data_file, index_col=0).sort_index()  # read calculation results to a dataframe
        full_name_list = list(self.full_pair_data_df)  # initialize data name list for later filter
        # apply structure filter
        if self.structure_filter != []:
            self.full_pair_data_df = self.full_pair_data_df.drop(self.structure_filter)
        
        # assert exp data match calc data
        assert list(self.expdata_df.index) == list(self.full_pair_data_df.index), 'cases do not match!'

        # collect name filters
        self.calc_type_filter = calc_type_filter
        self.major_minor_filter = major_minor_filter
        self.parameter_filter = parameter_filter
        self.total_filter_set = set(self.calc_type_filter + self.major_minor_filter + self.parameter_filter)
        self.data_name_list = []
        self.filted_name_list = []
        for head in full_name_list:  # filter by name
            if len(set(head.split('_')) & self.total_filter_set) == 0:
                self.data_name_list.append(head)
            else:
                self.filted_name_list.append(head)

        # apply name filters
        self.filtered_pair_data_df = self.full_pair_data_df.drop(self.filted_name_list, axis=1)

        # calculate p value and apply t_test filter
        self.t_test_filter = t_test_filter
        if self.t_test_filter:
            self.t_test_filted_name_list = []  # para names that do not pass t test
            for para in self.filtered_pair_data_df.keys()[1:]:
                if not t_value_test(self.filtered_pair_data_df[para], self.expdata_enantio_df):
                    self.t_test_filted_name_list.append(para)
                    self.data_name_list.remove(para)
            if self.t_test_filted_name_list != []:
                self.filtered_pair_data_df = self.filtered_pair_data_df.drop(self.t_test_filted_name_list, axis=1)
        
        self.structure_name_list = self.expdata_df.index

        # output new csv
        if output_new_csv:
            self.filtered_pair_data_df.to_csv(pair_data_file[:-4] + '_new.csv', index=True)
        
    def __len__(self):
        return len(self.expdata_df)
    
    def __getitem__(self,idx):
        reaction_ee = torch.tensor(self.expdata_enantio_df[idx])  # get exp ee value of reaction with idx (float to tensor) 
        reaction_para = torch.tensor(self.filtered_pair_data_df.iloc[idx])  # get computational parameters of reaction with idx (list to tensor)

        return reaction_para, reaction_ee
    
class MVLRdataloader():
    '''
    take dataset as input, according to input parameters(k-fold, random 10%, ...),
    output train expdf, paradf and test expdf, paradf
    achieved by index
    '''
    def __init__(self,
                 pairdataset,  # input dataset ready to be splited
                 k_fold=0,  # use k-fold cross-validation, e.g. k-fold=10, 10-fold cross validation,
                            # dataloader length will be 10, train-test will be 9-1
                 random_select=0,  # use random selection to split dataset, random=10 means 10% data will be in test set
                 remain_in_train=True,  # remainder data in train set or test set(False), affect both k-fold and random
                 ):
        
        self.dataset = pairdataset
        self.total_length = len(self.dataset)
        print('input dataset has {} items'.format(self.total_length))
        self.k_fold = k_fold
        assert self.k_fold >= 0, 'k_fold must be greater than or equal 0'
        assert self.k_fold <= self.total_length, 'k_fold must be smaller than dataset length'
        self.random_select = random_select
        assert 0 <= self.random_select < 100, 'random select must be in range of [0,100)'
        assert self.k_fold * self.random_select == 0, 'cannot choose k_fold and random select at the same time'
        self.remain_in_train = remain_in_train

    def __len__(self):
        if self.k_fold == 0:
            return 1
        else:
            return self.k_fold
    
    def __getitem__(self, idx):
        if self.k_fold > 0:
            fold_length = self.total_length // self.k_fold
            train_index_list = []
            test_index_list = []
            for k in range(self.k_fold):
                fold_index_list = [i for i in range(k * fold_length, (k+1) * fold_length)]
                if k == idx:
                    test_index_list += fold_index_list
                else:
                    train_index_list += fold_index_list

            train_name_list = [self.dataset.structure_name_list[i] for i in train_index_list]
            test_name_list = [self.dataset.structure_name_list[i] for i in test_index_list]
        
        elif self.random_select > 0:
            random_case_number = self.total_length * self.random_select // 100
            test_name_list = [self.dataset.structure_name_list[i] for i in random.sample(range(self.total_length), random_case_number)]

        else:
            test_name_list = []

        self.test_length = len(test_name_list)
        self.train_length = self.total_length - self.test_length
        print('test dataset has {} items \ntrain dataset has {} items'.format(self.test_length, self.train_length))
        testexpdf = self.dataset.expdata_enantio_df[test_name_list]
        trainexpdf = self.dataset.expdata_enantio_df.drop(test_name_list)

        testparadf = self.dataset.filtered_pair_data_df.loc[test_name_list]
        trainparadf = self.dataset.filtered_pair_data_df.drop(test_name_list)

        return trainexpdf, trainparadf, testexpdf, testparadf
