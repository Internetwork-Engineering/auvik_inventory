#!/usr/bin/env python

#title:             upgrade_pip.py
#description:       Upgrade PIP packages
#author:            Ricky Laney
#date:              20190503
#version:           0.0.1
#usage:             python upgrade_pip.py or ./upgrade_pip.py
#notes:             
#python_version:    3.7.0
#==============================================================================

import os
import re
import subprocess as sp

req_re = re.compile(r"require")
the_cwd = os.getcwd()

def get_project_dir():
    if 'util' in the_cwd.split('/')[-1:]:
        prj = os.path.dirname(the_cwd)
    else:
        prj = os.getcwd()
    return prj

def find_requirements(prj):
    if not os.getcwd() == prj: os.chdir(prj)
    if os.path.isdir(os.path.join(prj, 'requirements')):
        os.chdir(os.path.join(prj, 'requirements'))
        req_files = [ f for f in os.listdir(os.getcwd()) if f.endswith('txt') ]
    else:
        req_files = [ f for f in os.listdir(os.getcwd()) if f.endswith('txt') \
                      and f.__contains__('require') ]
    return req_files

def get_modules(req_files):
    mod_list = []
    for f in req_files:
        with open(f) as fd:
            for line in fd.readlines():
                if line.__contains__('=='):
                    sep = '=='
                elif line.__contains__('<='):
                    sep = '<='
                elif line.__contains__('>='):
                    sep = '>='
                else:
                    continue
                items = line.split(sep)
                mod = items[0]
                ver = items[1].split()[0]
                ln = {'mod': mod, 'ver': ver, 'sep': sep}
                if ln not in mod_list:
                    mod_list.append(ln)
    return sorted(mod_list, key=lambda mod: mod['mod'])

def write_upgrade(prj, mod_list):
    pip_up = os.path.join(prj, 'pip_upgrade.txt')
    if os.path.exists(pip_up):
        os.remove(pip_up)
    with open(pip_up, 'w+') as pip_up_fd:
        for mod in mod_list:
            pip_up_fd.write(f"{mod['mod']}{mod['sep']}{mod['ver']}\n")
    return pip_up


if __name__ == '__main__':
    prj = get_project_dir()
    reqs = find_requirements(prj)
    mod_list = get_modules(reqs)
    pip_up = write_upgrade(prj, mod_list)
    print(f"Now you can run pip install -U -r {pip_up}")

