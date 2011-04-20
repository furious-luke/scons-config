import sys, os
import Package
from Package import have_any_opts, try_link

parmetis_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <mpi.h>
#include <parmetis.h>
int main(int argc, char* argv[]) {
   return EXIT_SUCCESS;
}
'''

parmetis_libs=[['parmetis', 'metis']]

def CheckParMETIS(ctx, required=True):
    env = ctx.env
    ctx.Message('Checking for ParMETIS ... ')
    Package.check_options(env, 'ParMETIS')

    res = Package.CheckPkg(ctx, 'ParMETIS', parmetis_text, parmetis_libs)

    Package.Required('ParMETIS', res[0], required)
    ctx.Result(res[0])
    return res[0]

def AddOptions(vars):
    Package.AddOptions(vars, 'ParMETIS')
