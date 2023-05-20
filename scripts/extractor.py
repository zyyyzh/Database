'''
Discriptor extractor for ZS-CMJ

Author: Zihao Ye

CreateDate: 2023-02-23
Version: v0.1 2023-02-25

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


def extract_xtb_SPE(file_name):
    '''
    extract single point energy from xtb log file
    unit in Eh
    '''
    with open(file_name, 'r') as f:
        lines = f.readlines()
    
    for i in range(-1, -len(lines), -1):
        if 'TOTAL ENERGY' in lines[i]:
            # SPE = format(float(lines[i].split()[3]), '.6f')
            SPE = float(lines[i].split()[3])
            break
    
    return SPE

def extract_xtb_Grad(file_name):
    '''
    extract Gradient from xtb log file
    unit in Eh/α
    '''
    with open(file_name, 'r') as f:
        lines = f.readlines()
    
    for i in range(-1, -len(lines), -1):
        if 'GRADIENT NORM' in lines[i]:
            # Grad = format(float(lines[i].split()[3]), '.6f')
            Grad = float(lines[i].split()[3])
            break
    
    return Grad

def extract_xtb_Force(file_name):
    '''
    extract Force from xtb log file
    '''
    pass

def extract_xtb_Gap(file_name):
    '''
    extract HOMO-LUMO gap from xtb log file
    unit in eV
    '''
    with open(file_name, 'r') as f:
        lines = f.readlines()
    
    for i in range(-1, -len(lines), -1):
        if 'HOMO-LUMO GAP' in lines[i]:
            # Gap = format(float(lines[i].split()[3]), '.6f')
            Gap = float(lines[i].split()[3])
            break
    
    return Gap

def extract_xtb_charge(file_name, atom_idx):
    '''
    extract charge info from xtb charges file
    '''
    with open(file_name, 'r') as f:
        lines = f.readlines()

    # charge = format(float(lines[atom_idx-1]), '.6f')
    charge = float(lines[atom_idx-1])
    return charge

def extract_xtb_wbo(file_name, atom_idx1, atom_idx2):
    '''
    extract wbo info from xtb wbo file
    if atom_idx1 > atom_idx2, swap them
    if atom pair not in file, return 0
    '''
    if atom_idx1 > atom_idx2:
        atom_idx1, atom_idx2 = atom_idx2, atom_idx1

    with open(file_name, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.split()[0] == str(atom_idx1) and line.split()[1] == str(atom_idx2):
            return float(line.split()[2])
    
    return 0.0

def extract_xtb_ELUMO(file_name):
    '''
    extract LUMO energy from xtb log file
    unit in eV
    '''
    with open(file_name, 'r') as f:
        lines = f.readlines()
    
    for i in range(-1, -len(lines), -1):
        if '(LUMO)' in lines[i]:
            # ELUMO = format(float(lines[i].split()[-2]), '.4f')
            ELUMO = float(lines[i].split()[-2])
            break
    
    return ELUMO

def extract_xtb_EHOMO(file_name):
    '''
    extract HOMO energy from xtb log file
    unit in eV
    '''
    with open(file_name, 'r') as f:
        lines = f.readlines()
    
    for i in range(-1, -len(lines), -1):
        if '(HOMO)' in lines[i]:
            # EHOMO = format(float(lines[i].split()[-2]), '.4f')
            EHOMO = float(lines[i].split()[-2])
            break
    
    return EHOMO

def extract_gau_SPE(file_name):  # TODO: debug on rare cases
    '''
    extract single point energy from Gaussian log file
    '''
    with open(file_name) as f:
        gauf = f.readlines()
    
    end_idx = len(gauf)-2  # if no @ exist, read all lines
    for i in range(len(gauf)):
        if "@" in gauf[i]:
            end_idx = i
    gauf = gauf[:end_idx+1]

    try:
        for i in range(1,len(gauf)):
            if 'HF=' in gauf[-i]:
                tmplist = gauf[-i].split('\\')
                for j in range(len(tmplist)-1):
                    if 'HF=' in tmplist[j]:
                        spenergy = tmplist[j][3:].strip()
                if 'HF=' in tmplist[-1]:
                    nextlist = gauf[-i+1].split('\\')
                    spenergy = tmplist[-1][3:-1].strip() + nextlist[0].strip()
                break
            elif 'HF' in gauf[-i]:
                spenergy = gauf[-(i-1)].split('\\')[0].strip()[1:]
                break
            elif 'F=-' in gauf[-i]:
                spenergy = gauf[-i].split('\\')[0].strip()[2:]
                break
        spenergy = float(spenergy)
    except:
        spenergy = -1.0

    # spenergy = format(spenergy, '.6f')
    return spenergy

def extract_gau_Free_Energy(gau_file):
    '''
    get free energy data in gaussian output file
    if error occurs, return -1.0
    '''
    with open(gau_file) as f:
        gauf = f.readlines()
    
    free_correction = 0.0
    free_energy = 0.0
    try:
        for i in range(len(gauf)):
            if 'Thermal correction to Gibbs Free Energy=' in gauf[i]:
                free_correction = float(gauf[i].split()[-1])
            if 'Sum of electronic and thermal Free Energies=' in gauf[i]:
                free_energy = float(gauf[i].split()[-1])

    except:
        free_correction = -1.0
        free_energy = -1.0

    # free_correction = format(free_correction, '.6f')
    # free_energy = format(free_energy, '.6f')
    return free_correction, free_energy

def extract_gau_Force(model_name):
    '''
    extract Force from Gaussian log file
    '''
    with open(model_name) as f:
        gauf = f.readlines()
    gauf.reverse()

    force_rms = 0.0
    force_max = 0.0
    try:
        for i in range(len(gauf)):
            if 'Maximum Force' in gauf[i]:
                force_max = float(gauf[i].split()[2])
                break
            if 'RMS     Force' in gauf[i]:
                force_rms = float(gauf[i].split()[2])

    except:
        force_rms = -1.0
        force_max = -1.0

    # force_rms = format(force_rms, '.6f')
    # force_max = format(force_max, '.6f')

    return force_rms, force_max

def extract_gau_Charge(model_name, atom_idx):
    '''
    extract charge info from Gaussian log file
    '''
    with open(model_name) as f:
        gauf = f.readlines()
    gauf.reverse()

    charge = 0.0
    try:
        for i in range(len(gauf)):
            if 'Mulliken charges:' in gauf[i]:
                charge_idx = i
                break
        charge = float(gauf[charge_idx-atom_idx-1].split()[2])
    except:
        charge = -1.0

    # charge = format(charge, '.6f')
    return charge

def extract_gau_MO(fchk_file):
    '''
    extract EHOMO ELUMO gap from fchk file
    '''
    with open(fchk_file) as ff:
        fchkf = ff.readlines()
    
    Ehomo = 0.0
    Elumo = 0.0
    for i in range(len(fchkf)):
        if 'Number of electrons' in fchkf[i]:
            tot_electron = int(fchkf[i].split()[-1])
            if tot_electron%2 == 0:
                occ_orbital = tot_electron/2
            else:
                occ_orbital = tot_electron//2 + 1
            break
    
    orbital_idx = 0
    for i in range(len(fchkf)):
        if 'Alpha Orbital Energies ' in fchkf[i]:
            orbital_idx = i
            break
    
    HOMO_location = [int(occ_orbital//5), int(occ_orbital%5)]
    LUMO_location = [int((occ_orbital+1)//5), int((occ_orbital+1)%5)]

    if HOMO_location[1] == 0:
        homostr = fchkf[orbital_idx + HOMO_location[0]].split()[-1]
    else:
        homostr = fchkf[orbital_idx + HOMO_location[0] + 1].split()[HOMO_location[1] - 1]

    if LUMO_location[1] == 0:
        lumostr = fchkf[orbital_idx + LUMO_location[0]].split()[-1]
    else:
        lumostr = fchkf[orbital_idx + LUMO_location[0] + 1].split()[LUMO_location[1] - 1]

    # gap = format(float(homostr) - float(lumostr), '.6f')
    # Ehomo = format(float(homostr), '.6f')
    # Elumo = format(float(lumostr), '.6f')
    gap = float(homostr) - float(lumostr)
    Ehomo = float(homostr)
    Elumo = float(lumostr)
    
    return Ehomo, Elumo, gap

