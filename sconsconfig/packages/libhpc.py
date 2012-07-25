import sys, os
from Package import Package

##
##
##
class libhpc(Package):

    def __init__(self, **kwargs):
        defaults = {
            'download_url': '',
        }
        defaults.update(kwargs)
        super(libhpc, self).__init__(**defaults)
        self.ext = '.cc'
        self.libs=[
            ['hpc'],
        ]
        self.extra_libs=[
            [],
        ]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <mpi.h>
#include <libhpc/libhpc.hh>
int main(int argc, char* argv[]) {
   int rank;
   MPI_Init(&argc, &argv);
   printf("%d\n", MPI_VERSION);
   printf("%d\n", MPI_SUBVERSION);

   /* This will catch OpenMPI libraries. */
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);

   MPI_Finalize();
   return EXIT_SUCCESS;
}
'''

        # Setup the build handler. I'm going to assume this will work for all architectures.
        self.set_build_handler([
            'scons PREFIX=${PREFIX} install',
        ])

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for libhpc ... ')
        self.check_options(env)

        res = super(libhpc, self).check(ctx)

        self.check_required(res[0])
        ctx.Result(res[0])
        return res[0]
