import os
import sys
import argparse
# TODO: add similarity calculation and filter(RMSD) in conformation output 
# TODO: change cf output into a class
# TODO: add structure cluster method to cf class

num_to_ele = {'1': 'H', '2': 'He', '3': 'Li', '4': 'Be', '5': 'B', '6': 'C', '7': 'N', '8': 'O', '9': 'F', '10': 'Ne', '11': 'Na', '12': 'Mg', '13': 'Al', '14': 'Si', '15': 'P', '16': 'S', '17': 'Cl', '18': 'Ar', '19': 'K', '20': 'Ca', '21': 'Sc', '22': 'Ti', '23': 'V', '24': 'Cr', '25': 'Mn', '26': 'Fe', '27': 'Co', '28': 'Ni', '29': 'Cu', '30': 'Zn', '31': 'Ga', '32': 'Ge', '33': 'As', '34': 'Se', '35': 'Br', '36': 'Kr', '37': 'Rb', '38': 'Sr', '39': 'Y', '40': 'Zr', '41': 'Nb', '42': 'Mo', '43': 'Tc', '44': 'Ru', '45': 'Rh', '46': 'Pd', '47': 'Ag', '48': 'Cd', '49': 'In', '50': 'Sn', '51': 'Sb', '52': 'Te', '53': 'I', '54': 'Xe', '55': 'Cs', '56': 'Ba', '57': 'La', '58': 'Ce', '59': 'Pr', '60': 'Nd', '61': 'Pm', '62': 'Sm', '63': 'Eu', '64': 'Gd', '65': 'Tb', '66': 'Dy', '67': 'Ho', '68': 'Er', '69': 'Tm', '70': 'Yb', '71': 'Lu', '72': 'Hf', '73': 'Ta', '74': 'W', '75': 'Re', '76': 'Os', '77': 'Ir', '78': 'Pt', '79': 'Au', '80': 'Hg', '81': 'Tl', '82': 'Pb', '83': 'Bi', '84': 'Po', '85': 'At', '86': 'Rn', '87': 'Fr', '88': 'Ra', '89': 'Ac', '90': 'Th', '91': 'Pa', '92': 'U', '93': 'Np', '94': 'Pu', '95': 'Am', '96': 'Cm', '97': 'Bk', '98': 'Cf', '99': 'Es', '100': 'Fm', '101': 'Md', '102': 'No', '103': 'Lr', '104': 'Rf', '105': 'Db', '106': 'Sg', '107': 'Bh', '108': 'Hs', '109': 'Mt', '110': 'Ds', '111': 'Rg', '112': 'Cn', '113': 'Nh', '114': 'Fl', '115': 'Mc', '116': 'Lv', '117': 'Ts', '118': 'Og'}

def get_coord_elements(structure_list):
    '''
    extract all elements in coord
    '''
    element_list = []
    for line in structure_list:
        atom = line.split()[0]
        if atom.isdigit():
            ele = num_to_ele[atom]
        else:
            ele = atom
        element_list.append(ele)
    return set(element_list)
    
def get_model_file(model_file):
    # model_file = input('please input model file name:')
    with open(model_file) as mf:
        mflines = mf.readlines()
    emptyindex = []
    for i in range(len(mflines)):
        if mflines[i] == '\n':
            emptyindex.append(i)
    
    mfhead = mflines[:emptyindex[1]+2]
    mftail = mflines[emptyindex[2]:]
    return mfhead, mftail

def generate_gjf_file(structure_list, mfhead, mftail, ofile_name, chk_name=None, title=None, c_m=None):
    
    ofile_name = ofile_name.split('.')[0]  # modify output file name

    if title == None:  # blabalb # blabalb # blabalb
        title = ofile_name.split('/')[-1]
    if c_m != None:
        mfhead[-1] = c_m
    if chk_name == None:
        chk_name = ofile_name.split('/')[-1]
    
    mfhead[-3] = title + '\n'

    for i in range(len(mfhead)):  # add chk info
        if r'%chk=' in mfhead[i]:
            mfhead[i] = r'%chk=' + chk_name + '.chk\n'
            break
        if '#' in mfhead[i]:
            mfhead.insert(i, r'%chk=' + chk_name + '.chk\n')
            break

    basis_element_lineid = []
    element_dict = {}
    for j in range(len(mftail)):  # modify basis info accordingly
        if '****' in mftail[j]:
            if mftail[j-2].split()[-1] == '0':
                for ele in mftail[j-2].split()[:-1]:
                    element_dict[ele] = j-2  # get elements in model basis setting
                basis_element_lineid.append(j-2)
    
    if len(basis_element_lineid) > 0:  # basis part exist
        element_set = set(element_dict.keys())
        coord_element_set = get_coord_elements(structure_list)  # get elements in structure, output set
        basis_element_list = mftail[basis_element_lineid[0]].split()[:-1]
        if len(element_set.difference(coord_element_set)) > 0:
            for e in element_set.difference(coord_element_set):
                basis_element_list.remove(e)  # more elements in basis than coord, to be removed
        elif len(coord_element_set.difference(element_set)) > 0:
            for e in coord_element_set.difference(element_set):
                basis_element_list.append(e)  # more elements in coord than in basis, to be added
        else:
            pass
        basis_element_list.append('0')
        basis_element_line = ' '.join(basis_element_list) + '\n'
        mftail[basis_element_lineid[0]] = basis_element_line

    out_gjf_list = mfhead + structure_list + mftail
    with open(ofile_name+'.gjf', mode='w') as gjf:
        gjf.writelines(out_gjf_list)


def get_coord_from_gjf(gjf_file):
    '''
    read coord from gjf file
    include isotope info
    return list of coord
    '''
    with open(gjf_file) as gf:
        gflines = gf.readlines()
    emptyindex = []
    for i in range(len(gflines)):
        if gflines[i] == '\n':
            emptyindex.append(i)

    coord_list = gflines[emptyindex[1]+2:emptyindex[2]] 
    c_m = gflines[emptyindex[1]+1]# include charge and multiplicity
    return coord_list, c_m

def get_coord_from_cf_xyz(xyz_file):
    # xyz_file = input('please input xyz file name:')
    with open(xyz_file) as xf:
        xflines = xf.readlines()[2:]
    atomnum = int(xflines[0].strip())
    structure_len = atomnum + 4
    all_structure_list = [xflines[d:d+structure_len] for d in range(0, len(xflines), structure_len)]
    for n in range(len(all_structure_list)):
        all_structure_list[n] = [line for line in all_structure_list[n] if line.strip() !='']
    # print(len(all_structure_list[0]))
    # print(all_structure_list[5])
    all_structure_dict = {all_structure_list[i][1].split()[1]:all_structure_list[i][2:] for i in range(len(all_structure_list))}
    all_title_dict = {all_structure_list[i][1].split()[1]:all_structure_list[i][1] for i in range(len(all_structure_list))}
    # print('total structure:', len(all_structure_dict))
    return all_structure_dict, all_title_dict

def get_coord_from_irc(irc_file):
    with open(irc_file) as ircf:
        irclines = ircf.readlines()
    structure_index_list = []
    for i in range(len(irclines)):
        if 'NAtoms= ' in irclines[i]:
            atomnum = int(irclines[i].split()[1])
        if 'Input orientation:' in irclines[i]:
            structure_index_list.append(i)
    structure_index_list = structure_index_list[:-1]
    
    ircpoints = int(len(structure_index_list))
    print(ircpoints)
    all_structure_list = [irclines[d+5:d+5+atomnum] for d in structure_index_list]
    for n in range(len(all_structure_list)):
        for m in range(atomnum):
            tmplist = all_structure_list[n][m].split()[1:]
            all_structure_list[n][m] = '  '.join(tmplist) + '\n'
    
    reorg_structure_list = [all_structure_list[-i] for i in range(1, (ircpoints+1)//2)] + all_structure_list[:(ircpoints+1)//2]
    
    all_structure_dict = {str(i+1):reorg_structure_list[i] for i in range(len(reorg_structure_list))}
    all_title_dict = {str(i+1):'point ' + str(i+1) + ' ' + irc_file + '\n' for i in range(len(reorg_structure_list))}
    return all_structure_dict, all_title_dict
    
def get_coord_from_log(log_file):
    '''
    read coords from log file's final structure
    '''
    with open(log_file) as logf:
        loglines = logf.readlines()
    structure_index_list = []
    for i in range(len(loglines)):
        if 'NAtoms= ' in loglines[i]:
            atomnum = int(loglines[i].split()[1])
        if 'Input orientation:' in loglines[i]:
            structure_index_list.append(i)
    structure_index = structure_index_list[-1]

    coord_list = loglines[structure_index+5:structure_index+5+atomnum]
    for m in range(atomnum):
        tmplist = coord_list[m].split()[1:]
        coord_list[m] = '  '.join(tmplist) + '\n'
    return coord_list

def get_coord_from_single_xyz(xyz_file):
    with open(xyz_file) as xf:
        xflines = xf.readlines()
    atomnum = int(xflines[0].strip())
    return xflines[2:atomnum+3]


def from_cf_to_gjf(xyz_file, model_file, selection_list=None):
    xyz_preflix = xyz_file.split('.')[0]
    mfhead, mftail = get_model_file(model_file)
    all_structure_dict, all_title_dict = get_coord_from_cf_xyz(xyz_file)
    if selection_list == None:
        selection_list = input('please input selected structure tstmpe numbers:(seperate by spaces)').split()
    if selection_list == []:
        selection_list = all_structure_dict.keys()
    for tstmpe in selection_list:
        generate_gjf_file(all_structure_dict[tstmpe], mfhead, mftail, 
        xyz_preflix + '-' + tstmpe.rjust(5,'0'))

def from_irc_to_gjf(irc_file, model_file, split_index=None):
    irc_preflix = irc_file.split('.')[0]
    if split_index is None:
        mfhead, mftail = get_model_file(model_file)
        all_structure_dict, all_title_dict = get_coord_from_irc(irc_file)
        for points in all_structure_dict.keys():
            generate_gjf_file(all_structure_dict[points], mfhead, mftail,
             irc_preflix+'-p'+points.rjust(3,'0'), chk_name=irc_preflix+'-p'+points.rjust(3,'0'), title=all_title_dict[points])
    else: 
        split_index = int(split_index)
        assert len(model_file) == 2, 'a list including two model files needed!'
        mfhead_a, mftail_a = get_model_file(model_file[0])
        mfhead_b, mftail_b = get_model_file(model_file[1])
        all_structure_dict, all_title_dict = get_coord_from_irc(irc_file)
        for points in all_structure_dict.keys():
            generate_gjf_file(all_structure_dict[points][:split_index], mfhead_a, mftail_a,
             irc_preflix+'-a-p'+points.rjust(3,'0'), chk_name=irc_preflix+'-a-p'+points.rjust(3,'0'), title='a-'+all_title_dict[points])
            generate_gjf_file(all_structure_dict[points][split_index:], mfhead_b, mftail_b,
             irc_preflix+'-b-p'+points.rjust(3,'0'), chk_name=irc_preflix+'-b-p'+points.rjust(3,'0'), title='b-'+all_title_dict[points])
    
def from_log_to_gjf(log_file, model_file, ofile_name=None):
    '''
    get coord from the last structure in a log file
    output new gjf based on this structure and a model file
    '''
    coord_list = get_coord_from_log(log_file)
    mfhead, mftail = get_model_file(model_file)
    if ofile_name == None:
        ofile_name = log_file.split('.')[-2]
    
    generate_gjf_file(coord_list, mfhead, mftail, ofile_name)

def from_gjf_to_gjf(inp_gjf, model_file, ofile_name=None):
    '''
    get coord from a gjf file
    output new gjf based on this structure and a model file
    '''
    coord_list, c_m = get_coord_from_gjf(inp_gjf)
    mfhead, mftail = get_model_file(model_file)
    if ofile_name == None:
        ofile_name = inp_gjf
    
    generate_gjf_file(coord_list, mfhead, mftail, ofile_name, c_m=c_m)

def from_gjf_to_xyz(inp_gjf, ofile_name=None):
    '''
    get coord from a gjf file
    output xyz file
    '''
    coord_list, c_m = get_coord_from_gjf(inp_gjf)
    atom_num = len(coord_list)
    if ofile_name == None:
        ofile_name = inp_gjf.split('.')[0]
    with open(ofile_name + '.xyz', 'w') as of:
        of.write(str(atom_num) + '\n')
        of.write(inp_gjf.split('.')[0] + '\n')
        of.writelines(coord_list)

def from_xyz_to_gjf(inp_xyz, model_file, ofile_name=None):
    '''
    get coord from a xyz file
    output gjf file
    '''
    coord_list = get_coord_from_single_xyz(inp_xyz)
    mfhead, mftail = get_model_file(model_file)
    if ofile_name == None:
        ofile_name = inp_xyz
    
    generate_gjf_file(coord_list, mfhead, mftail, ofile_name)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        '--log_file', '-l',
        type=str,
        help='log file used in from_log_to_gjf',
        default=None,
        )
    p.add_argument(
        '--ofile_name',
        type=str,
        help='output file name in from_log_to_gjf, optional',
        default=None
    )
    p.add_argument(
        '--model_gjf', '-m',
        type=str,
        help='model gjf file used in all funcs',
        default=None,
    )
    p.add_argument(
        '--gjf_file', '-g',
        type=str,
        help='inp gjf file used in from_gjf_to_gjf',
        default=None,
    )
    p.add_argument(
        '--irc_file', '-i',
        type=str,
        help='irc log file used in from_irc_to_gjf',
        default=None,
    )
    p.add_argument(
        '--split_index',
        type=int,
        help='split index used in from_irc_to_gjf, optional',
        default=None,
    )
    p.add_argument(
        '--cf_file', '-c',
        type=str,
        help='conformation search output xyz file used in from_cf_to_gjf',
        default=None,
    )
    p.add_argument(
        '--xyz_file', '-x',
        type=str,
        help='inp_xyz file used in from_xyz_to_gjf',
        default=None,
    )
    p.add_argument(
        '--type','-t',
        type=str,
        help='''
        job type, currently can choose from: cf, irc, log, gjf.\n\n

        if cf\n
        --cf_file and --model_gjf are needed\n
        from_cf_to_gjf() will run, you will have to further input tstmpe number;\n\n
        
        if irc\n
        --irc_file and --model_gjf are needed, --split_index is optional\n
        from_irc_to_gjf() will run;\n\n

        if log\n
        --log_file and --model_gjf are needed, --ofile_name is optional\n
        from_log_to_gjf() will run;\n\n
        
        if gjf\n
        --gjf_file and --model_gjf are needed, --ofile_name is optional\n
        from_gjf_to_gjf() will run;\n\n

        if gjf2xyz\n
        --gjf_file is needed, --ofile_name is optional\n
        from_gjf_to_xyz() will run;\n\n
        
        if xyz2gjf\n
        --xyz_file and --model_gjf are needed, --ofile_name is optional\n
        from_xyz_to_gjf() will run;\n\n
        ''',
        default=None,
    )

    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()

    log_file = args.log_file
    ofile_name = args.ofile_name
    model_gjf = args.model_gjf
    gjf_file = args.gjf_file
    irc_file = args.irc_file
    split_index = args.split_index
    cf_file = args.cf_file
    xyz_file = args.xyz_file

    if args.type == None:
        print('Please input job type! \n you can type batchgjf --help for help')

    elif args.type == 'cf':
        assert os.path.isfile(cf_file), 'please input cf_file !'
        assert os.path.isfile(model_gjf), 'please input model_gjf !'
        from_cf_to_gjf(cf_file, model_gjf)

    elif args.type == 'irc':
        assert os.path.isfile(irc_file), 'please input irc_file !'
        assert os.path.isfile(model_gjf), 'please input model_gjf !'
        from_irc_to_gjf(irc_file, model_gjf, split_index)

    elif args.type == 'log':
        assert os.path.isfile(log_file), 'please input log_file !'
        assert os.path.isfile(model_gjf), 'please input model_gjf !'
        from_log_to_gjf(log_file, model_gjf, ofile_name)

    elif args.type == 'gjf':
        assert os.path.isfile(gjf_file), 'please input gjf_file !'
        assert os.path.isfile(model_gjf), 'please input model_gjf !'
        from_gjf_to_gjf(gjf_file, model_gjf, ofile_name)

    elif args.type == 'gjf2xyz':
        assert os.path.isfile(gjf_file), 'please input gjf_file !'
        from_gjf_to_xyz(gjf_file, ofile_name)

    elif args.type == 'xyz2gjf':
        assert os.path.isfile(xyz_file), 'please input xyz_file !'
        assert os.path.isfile(model_gjf), 'please input model_gjf !'
        from_xyz_to_gjf(xyz_file, model_gjf, ofile_name)