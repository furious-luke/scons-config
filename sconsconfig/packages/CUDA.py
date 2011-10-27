import sys, os
from Package import Package


class CUDA(Package):

    def __init__(self, **kwargs):
        super(CUDA, self).__init__(**kwargs)
        self.cuda_compilers = ['nvcc']
        self.libs=[
            ['mpich'],
            ['pmpich', 'mpich'],
            ['mpich', 'mpl'],
            ['mpi'],
        ]
        self.extra_libs=[
            [],
            ['rt'],
            ['pthread', 'rt'],
            ['dl'],
            ['dl', 'rt'],
            ['dl', 'pthread'],
            ['dl', 'pthread', 'rt']
        ]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <mpi.h>
int main(int argc, char* argv[]) {
   MPI_Init(&argc, &argv);
   printf("%d\n", MPI_VERSION);
   printf("%d\n", MPI_SUBVERSION);
   MPI_Finalize();
   return EXIT_SUCCESS;
}
'''

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
