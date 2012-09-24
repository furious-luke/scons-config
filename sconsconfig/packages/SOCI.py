import sys, os
from Package import Package
import sconsconfig as config

class SOCI(Package):

    def __init__(self, **kwargs):
        defaults = {
            'download_url': 'http://downloads.sourceforge.net/project/soci/soci/soci-3.1.0/soci-3.1.0.zip',
        }
        defaults.update(kwargs)
        super(SOCI, self).__init__(**defaults)
        self.ext = '.cc'
        self.sub_dirs = [
            (('include', 'include/soci'), 'lib'),
            (('include', 'include/soci'), 'lib64'),
        ]
        self.libs=[
            ['soci_core']
        ]
        self.extra_libs=[
        ]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <soci/soci.h>
int main(int argc, char* argv[]) {
   return EXIT_SUCCESS;
}
'''

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for SOCI ... ')
        self.check_options(env)

        # SOCI can use Boost, so check to see if Boost is in our
        # set of configuration options and set accordingly.
        cmake = 'cmake -DCMAKE_INSTALL_PREFIX:PATH=${PREFIX}'
        boost = config.package(config.packages.boost)
        # if boost and boost.found and boost.base_dir:
        #     cmake += ' -DBOOST_DIR:PATH=' + boost.base_dir
        cmake += ' -DWITH_BOOST=off'

        # Check for sqlite3, like boost.
        sqlite = config.package(config.packages.sqlite3)
        if sqlite and sqlite.found:
            cmake += ' -DSQLITE3_INCLUDE_DIR:PATH=' + sqlite.include_directories()
            cmake += ' -DSQLITE3_LIBRARIES:PATH=' + sqlite.libraries()

        cmake += ' .'
        self.set_build_handler([
            cmake,
            'make',
            'make install'
        ])

        # Check each backend for existence.
        backends = {
            'sqlite3': {
                'libs': ['soci_core', 'soci_sqlite3'],
            },
            'mysql': {
                'libs': ['soci_core', 'soci_mysql'],
                'extra_libs': ['dl', 'mysqlclient'],
            },
        }
        found = False
        for be, opts in backends.iteritems():
            self.libs = [opts['libs']]
            self.extra_libs = [opts.get('extra_libs', [])]
            res = super(SOCI, self).check(ctx)
            if res[0]:
                found = True
                env.MergeFlags('-DHAVESOCI' + be.upper())

        self.check_required(found, ctx)
        ctx.Result(found)
        return found
