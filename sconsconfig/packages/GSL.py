import sys, os
from Package import Package


class GSL(Package):

    def __init__(self, **kwargs):
        super(GSL, self).__init__(**kwargs)
        self.libs=[
            ['gsl', 'gslcblas'],
            ['gsl'],
        ]
        self.extra_libs=[]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <gsl/gsl_version.h>
int main(int argc, char* argv[]) {
   return EXIT_SUCCESS;
}
'''

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for GSL ... ')
        self.check_options(env)

        res = super(GSL, self).check(ctx)

        self.check_required(res[0])
        ctx.Result(res[0])
        return res[0]
