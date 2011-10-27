import sys, os
from Package import Package

class PTScotch(Package):

    def __init__(self, **kwargs):
        super(PTScotch, self).__init__(**kwargs)
        self.libs=[['ptscotch', 'ptscotcherr', 'ptscotcherrexit', 'scotch', 'scotcherr', 'scotcherrexit']]
        self.extra_libs=[['z', 'm'],
                         ['z', 'm', 'rt']]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <mpi.h>
#include <ptscotch.h>
int main(int argc, char* argv[]) {
   return EXIT_SUCCESS;
}
'''

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for PTScotch ... ')
        self.check_options(env)

        res = super(PTScotch, self).check(ctx)

        self.check_required(res[0], ctx)
        ctx.Result(res[0])
        return res[0]
