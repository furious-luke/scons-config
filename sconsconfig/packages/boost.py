import sys, os
from Package import Package

class boost(Package):

    def __init__(self, **kwargs):
        super(boost, self).__init__(**kwargs)
        self.sub_dirs = [('', ''), ('include', '')]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <boost/optional.hpp>
int main(int argc, char* argv[]) {
   return EXIT_SUCCESS;
}
'''
        self.ext = '.cc'

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for boost ... ')
        self.check_options(env)

        res = super(boost, self).check(ctx)

        self.check_required(res[0], ctx)
        ctx.Result(res[0])
        return res[0]
