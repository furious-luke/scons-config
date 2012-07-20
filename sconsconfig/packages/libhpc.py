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
        super(MPI, self).__init__(**defaults)
        self.libs=[
            ['hpc'],
        ]
        self.extra_libs=[
            [],
        ]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <libhpc.h>
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
            './configure --prefix=${PREFIX} --enable-shared --disable-fc --disable-f77',
            'make',
            'make install'
        ])

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for MPI ... ')
        self.check_options(env)

        if os.path.split(ctx.env['CC'])[1] in self.mpi_compilers:
            if self.have_any_options(env, 'MPI_DIR', 'MPI_INC_DIR', 'MPI_LIB_DIR', 'MPI_LIBS'):
                print '\n'
                print 'Cannot supply options for locating an MPI installation in'
                print 'combination with using an MPI compiler.\n'
                env.Exit()

            res = self.try_link(ctx)
            if not res[0]:
                print '\n'
                print 'Was unable to use the MPI compiler:'
                print '  %s'%ctx.env['CC']
                env.Exit()

        else:
            res = super(MPI, self).check(ctx)

        self.check_required(res[0])
        ctx.Result(res[0])
        return res[0]
