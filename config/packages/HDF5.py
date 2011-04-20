import sys, os
import Package
from Package import have_any_opts, try_link

hdf5_text1 = r'''
#include <stdlib.h>
#include <stdio.h>
#include <mpi.h>
#include <hdf5.h>
int main(int argc, char* argv[]) {
   hid_t plist_id, file_id;
   MPI_Init(&argc, &argv);
   plist_id = H5Pcreate(H5P_FILE_ACCESS);
   H5Pset_fapl_mpio(plist_id, MPI_COMM_WORLD, MPI_INFO_NULL);
   file_id = H5Fcreate("'''
hdf5_text2 = r'''", H5F_ACC_TRUNC, H5P_DEFAULT, plist_id);
   H5Pclose(plist_id);
   H5Fclose(file_id);
   printf("%d\n", H5_VERS_MAJOR);
   printf("%d\n", H5_VERS_MINOR);
   printf("%d\n", H5_VERS_RELEASE);
   MPI_Finalize();
   return EXIT_SUCCESS;
}
'''

hdf5_libs=['hdf5']
hdf5_extra_libs=[[],
                 ['z'],
                 ['m'],
                 ['z', 'm']]

def CheckHDF5(ctx, required=True):
    env = ctx.env
    ctx.Message('Checking for HDF5 ... ')
    Package.check_options(env, 'HDF5')

    text = hdf5_text1 + os.path.join(ctx.sconf.confdir.path, 'test.h5') + hdf5_text2
    res = Package.CheckPkg(ctx, 'HDF5', text, hdf5_libs, hdf5_extra_libs)

    Package.Required('HDF5', res[0], required)
    ctx.Result(res[0])
    return res[0]

def AddOptions(vars):
    Package.AddOptions(vars, 'HDF5')
