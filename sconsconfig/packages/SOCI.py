import sys, os
from Package import Package

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
        self.set_build_handler([
            'cmake -DCMAKE_INSTALL_PREFIX:PATH=${PREFIX} .',
            'make',
            'make install'
        ])

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for SOCI ... ')
        self.check_options(env)

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
