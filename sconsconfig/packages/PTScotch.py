import sys, os
from Package import Package

class PTScotch(Package):

    def __init__(self, **kwargs):
        self.download_url = 'https://gforge.inria.fr/frs/download.php/28977/scotch_5.1.12b.tar.gz'
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

        # Setup the build handlers. Thanks to the way PTScotch is setup we will need a unique one of these
        # for every bloody architecture under the sun.
        self.set_build_handler([
            'cd src',
            'cp Make.inc/Makefile.inc.linux2',
            'sed ', # remove PTHREAD
        ])
        self.set_build_handler([
            'cd src',
            'cp Make.inc/Makefile.inc.darwin8',
            'sed ', # remove PTHREAD
        ], 'Darwin')

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for PTScotch ... ')
        self.check_options(env)

        res = super(PTScotch, self).check(ctx)

        self.check_required(res[0], ctx)
        ctx.Result(res[0])
        return res[0]
