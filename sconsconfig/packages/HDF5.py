import sys, os
from Package import Package


class HDF5(Package):

    def __init__(self, **kwargs):
        defaults = {
            'download_url': 'http://www.hdfgroup.org/ftp/HDF5/current/src/hdf5-1.8.9.tar.gz',
        }
        defaults.update(kwargs)
        super(HDF5, self).__init__(**defaults)
        self.parallel = kwargs.get('parallel', True)
        self.libs=[
            'hdf5',
            {'libraries': 'hdf5', 'prepend': False},
        ]
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

        # Setup the build handler. I'm going to assume this will work for all architectures.
        self.set_build_handler([
            './configure --prefix=${PREFIX} --enable-shared --enable-parallel CC=${MPI_DIR}/bin/mpicc',
            'make',
            'make install'
        ])

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for HDF5 ... ')
        self.check_options(env)

        res = super(HDF5, self).check(ctx)

        self.check_required(res[0])
        ctx.Result(res[0])
        return res[0]
