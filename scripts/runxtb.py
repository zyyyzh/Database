import os
import sys

def submit_xtb_job(xyz_name, charge=0, uhf=0, inp_name='', job_type='sp'):
    '''
    Submit a single xtb job
    default charge is 0, default uhf is 0
    use gfn2-xTB for the calculation
    default not input file
    default output file is {xyz_name}-out.xyz
    '''
    out_name = xyz_name.split('.')[0] + '-out.xyz'
    log_name = xyz_name.split('.')[0] + '.log'
    chrg_name = xyz_name.split('.')[0] + '.charges'
    wbo_name = xyz_name.split('.')[0] + '.wbo'

    if not os.path.exists(inp_name):
        print('input file not found!')
        inp_name = None

    if job_type == 'sp':
        if inp_name is None:
            xtbcmd = 'xtb {xyz_name} --gfn2 --chrg {charge} --uhf {uhf} > {log_name}'.format(xyz_name=xyz_name, charge=charge, uhf=uhf, log_name=log_name)
        else:
            xtbcmd = 'xtb {xyz_name} --gfn2 --chrg {charge} --uhf {uhf} --input {inp_name} > {log_name}'.format(xyz_name=xyz_name, charge=charge, uhf=uhf, inp_name=inp_name, log_name=log_name)
        try:
            os.system(xtbcmd)
            os.system('mv charges {chrg_name}'.format(chrg_name=chrg_name))  # rename output charges
            os.system('mv wbo {wbo_name}'.format(wbo_name=wbo_name))  # rename output wbo
            os.system('rm -f xtbrestart xtbtopo.mol')
        except Exception as e:
            print('xtb sp calculation failed for {xyz_name}'.format(xyz_name=xyz_name))
            print(e)
        else:
            print('xtb sp calculation finished for {xyz_name}'.format(xyz_name=xyz_name))

    elif job_type == 'opt':
        if inp_name is None:
            xtbcmd = 'xtb {xyz_name} --gfn2 --chrg {charge} --uhf {uhf} --opt > {log_name}'.format(xyz_name=xyz_name, charge=charge, uhf=uhf, log_name=log_name)
        else:
            xtbcmd = 'xtb {xyz_name} --gfn2 --chrg {charge} --uhf {uhf} --opt --input {inp_name} > {log_name}'.format(xyz_name=xyz_name, charge=charge, uhf=uhf, inp_name=inp_name, log_name=log_name) 
        os.system(xtbcmd)
        if os.path.exists('.xtboptok'):
            os.system('mv xtbopt.xyz {out_name}'.format(out_name=out_name))  # rename output structure
            os.system('mv charges {chrg_name}'.format(chrg_name=chrg_name))  # rename output charges
            os.system('mv wbo {wbo_name}'.format(wbo_name=wbo_name))  # rename output wbo
            os.system('rm -f .xtboptok xtbrestart xtbtopo.mol xtbopt.log')
            print('xtb opt calculation finished for {xyz_name}'.format(xyz_name=xyz_name))
        else:
            print('xtb opt calculation failed for {xyz_name}'.format(xyz_name=xyz_name))
    else:
        print('Job type not recognized')


if __name__ == '__main__':
    xyz_name = sys.argv[1]
    charge = int(sys.argv[2])
    uhf = int(sys.argv[3])
    inp_name = sys.argv[4]
    job_type = sys.argv[5]
    submit_xtb_job(xyz_name, charge, uhf, inp_name, job_type)
