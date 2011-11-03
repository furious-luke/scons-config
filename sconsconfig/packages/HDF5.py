import sys, os
from Package import Package


class HDF5(Package):

    def __init__(self, **kwargs):
        super(HDF5, self).__init__(**kwargs)
        self.parallel = kwargs.get('parallel', True)
        self.libs=[['hdf5']]
        if self.parallel:
            # Sometimes we see a problem with MPICH2 where the MPL library is included by libhdf5.so too
            # soon in the link command, causing issues with libmpich.so.
            self.libs.append(['mpl', 'mpich', 'hdf5'])
        self.extra_libs=[
            [], ['z'], ['m'], ['z', 'm'],
        ]
        if self.parallel:
            self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <hdf5.h>
#include <mpi.h>
int main(int argc, char* argv[]) {
   hid_t plist_id, file_id;
   int rank;
   MPI_Init(&argc, &argv);
   MPI_Comm_rank(MPI_COMM_WORLD, &rank);
   MPI_Finalize();
   return EXIT_SUCCESS;
}
'''
        else:
            self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <hdf5.h>
int main(int argc, char* argv[]) {
   hid_t plist_id, file_id;
   return EXIT_SUCCESS;
}
'''

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for HDF5 ... ')
        self.check_options(env)

        res = super(HDF5, self).check(ctx)

        self.check_required(res[0])
        ctx.Result(res[0])
        return res[0]
