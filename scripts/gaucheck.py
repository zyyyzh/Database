# check gaussian output file status
# Author: Zihao Ye
# creation time: April, 2023

import os
import sys


def get_termination(gau_file):
    '''
    judge whether the job has terminated normally
    '''
    with open(gau_file) as f:
        gauf = f.readlines()

    is_normal = 0 
    try:
        for i in range(1,10):
            if 'Normal termination' in gauf[-i]:
                is_normal = 1
                break
    except:
        is_normal = 0

    return is_normal

def gaucheck(dir=os.getcwd()):
    '''
    check all log or out file in dir
    if all normal termination, create .gaucheckok file and return 'ALL NORMAL'
    else return abnormal file list
    '''
    cwd = os.getcwd()
    if dir != cwd:
        os.chdir(dir)

    # gat log file list
    gau_list = [os.path.abspath(dir + '/' + file) for file in os.listdir(dir) if file.endswith('.log') or file.endswith('.out')]

    all_normal = 1
    abnormal_list = []
    for file in gau_list:
        if get_termination(file):
            pass
        else:
            all_normal = 0
            abnormal_list.append(file)
    
    if all_normal:
        with open(os.path.join(dir,'.gaucheckok'), 'w') as f:
            f.write('all normal')
        os.chdir(cwd)
        return 'ALL NORMAL'
    else:
        os.chdir(cwd)
        return abnormal_list

if __name__ == '__main__':
    gaucheck(sys.argv[1])