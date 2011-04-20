import sys, os
from distutils import sysconfig
import Package
from Package import have_any_opts, try_link

petsc_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <mpi.h>
#include <petsc.h>
int main(int argc, char* argv[]) {
   PetscInitialize(&argc, &argv, PETSC_NULL, PETSC_NULL);
   printf("%d\n", MPI_VERSION);
   printf("%d\n", MPI_SUBVERSION);
   PetscFinalize();
   return EXIT_SUCCESS;
}
'''

petsc_libs=[['petsc'], ['petscksp', 'petscvec', 'petsc']]
petsc_extra_libs = []

def parse_conf(ctx, conf_path, lib_dirs, libs):
    vars = {}
    sysconfig.parse_makefile(conf_path, vars)
    flag_dict = ctx.env.ParseFlags(vars['PACKAGES_LIBS'])
    lib_dirs.extend(flag_dict['LIBPATH'])
    for ii in range(len(libs)):
        libs[ii].extend(flag_dict['LIBS'])

def find_conf(ctx, base, inc_dirs, lib_dirs, libs, extra_libs):
    # PETSc 3.1
    conf_path = os.path.join(base, 'conf', 'petscvariables')
    if os.path.exists(conf_path):
        parse_conf(ctx, conf_path, lib_dirs, libs)

    # PETSC 2.3.3
    conf_path = os.path.join(base, 'bmake', 'petscconf')
    if os.path.exists(conf_path):
        vars = {}
        sysconfig.parse_makefile(conf_path, vars)
        if 'PETSC_ARCH' in vars:
            arch = vars['PETSC_ARCH']
            inc_dirs.extend([os.path.join(base, 'bmake', arch)])
            lib_dirs.extend([os.path.join(base, 'lib', arch)])
            conf_path = os.path.join(base, 'bmake', arch, 'petscconf')
            parse_conf(ctx, conf_path, lib_dirs, libs)

def CheckPETSc(ctx, required=True):
    env = ctx.env
    ctx.Message('Checking for PETSc ... ')
    Package.check_options(env, 'PETSc')

    res = Package.CheckPkg(ctx, 'PETSc', petsc_text, petsc_libs, petsc_extra_libs, loc_callback=find_conf)

    Package.Required('PETSc', res[0], required)
    ctx.Result(res[0])
    return res[0]

def AddOptions(vars):
    Package.AddOptions(vars, 'PETSc')
