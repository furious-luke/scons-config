import sys, os
from Package import Package

class rapidxml(Package):

    def __init__(self, **kwargs):
        defaults = {
            'download_url': '',
        }
        defaults.update(kwargs)
        super(rapidxml, self).__init__(**defaults)
        self.ext = '.cc'
        self.sub_dirs = [('', ''), ('include', '')]
        self.check_text = r'''
#include <stdlib.h>
#include <stdio.h>
#include <rapidxml.hpp>
int main(int argc, char* argv[]) {
   return EXIT_SUCCESS;
}
'''
        # self.set_build_handler([
        #     './bootstrap.sh',
        #     '!./b2 install --prefix=${PREFIX}'
        # ])

    def check(self, ctx):
        env = ctx.env
        ctx.Message('Checking for rapidxml ... ')
        self.check_options(env)

        res = super(rapidxml, self).check(ctx)

        self.check_required(res[0], ctx)
        ctx.Result(res[0])
        return res[0]
