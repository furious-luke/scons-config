import os, sys, copy
from config.utils import conv


def env_backup(env, names):
    '''
    Backup a set of environment macros.
    '''
    names = conv.to_iter(names)
    bkp = {}
    for n in names:
        if n not in env:
            bkp[n] = None
        else:
            bkp[n] = env[n]
    return bkp


def env_setup(env, **kw):
    '''
    Backup the existing environment and update with provided
    keywords.
    '''
    bkp = env_backup(env, kw.keys())
    env.Replace(**kw)
    return bkp


def env_restore(env, bkp):
    '''
    Restore a set of environment macros previously
    backed up with env_backup.
    '''
    for n, v in bkp.iteritems():
        if v is None:
            del env[n]
        else:
            env[n] = v


class Package(object):

    DEFAULT_SUB_DIRS = [('include', 'lib'), ('include', 'lib64')]

    def __init__(self, required=True):
        self.name = self.__class__.__name__
        self.required = required
        self.libs = []
        self.extra_libs = []
        self.sub_dirs = self.DEFAULT_SUB_DIRS
        self.check_text = ''
        self.options = []
        self.test_names = ['Check' + self.name]
        self.custom_tests = {'Check' + self.name: self.check}
        self.auto_add_libs=True
        self.run=True
        self.ext = '.c'

    def check(self, ctx, **kwargs):
        env = ctx.env
        name = self.name
        libs = self.get_libs()
        extra_libs = self.get_extra_libs()
        sub_dirs = self.get_sub_dirs()

        upp = name.upper()
        if self.have_option(env, upp + '_DIR'):
            res = self.try_location(ctx, self.get_option(env, upp + '_DIR'), **kwargs)
            if not res[0]:
                print '\n'
                print 'Unable to find a valid %s installation at:'%name
                print '  %s\n'%self.get_option(env, upp + '_DIR')
                env.Exit()

        elif self.have_any_options(env, upp + '_INC_DIR', upp + '_LIB_DIR', upp + '_LIBS'):
            inc_dirs = self.get_option(env, upp + '_INC_DIR').split(';')
            lib_dirs = self.get_option(env, upp + '_LIB_DIR').split(';')
            if self.have_option(env, upp + '_LIBS'):
                cur_libs = [map(env.File, self.get_option(env, upp + '_LIBS').split(';'))]
                cur_extra_libs = []
            else:
                cur_libs = libs
                cur_extra_libs = extra_libs

            res = self.try_location(ctx, '', **kwargs)
            if not res[0]:
                print '\n'
                print 'Unable to find a valid %s installation using:'%name
                if self.have_option(env, upp + '_INC_DIR'):
                    print '  Header directories: %s'%repr(inc_dirs)
                if self.have_option(env, upp + '_LIB_DIR'):
                    print '  Library directories: %s'%repr(lib_dirs)
                if self.have_option(env, upp + '_LIBS'):
                    print '  Libraries: %s'%repr([l.path for l in cur_libs])
                print
                env.Exit()

        else:
            common_dirs = ['/usr/local', os.environ['HOME'], os.path.join(os.environ['HOME'], 'soft'),
                       '/sw']
            res = (0, '')
            for cd in common_dirs:
                if not os.path.exists(cd):
                    continue
                for d in os.listdir(cd):
                    if d.find(name) == -1 and d.find(name.lower()) == -1 and d.find(name.upper()) == -1:
                        continue
                    d = os.path.join(cd, d)
                    if not os.path.isdir(d):
                        continue
                    res = self.try_location(ctx, d, **kwargs)
                    if res[0]:
                        break
                if res[0]:
                    break

            if res[0]:
                env[upp + '_DIR'] = d

        return res

    def check_required(self, result):
        name = self.name
        upp = name.upper()
        if not result and self.required:
            print '\n'
            print 'Unable to locate required package %s. You can specify'%name
            print 'the location using %s_DIR or a combination of'%upp
            print '%s_INC_DIR, %s_LIB_DIR and %s_LIBS.\n'%(upp, upp, upp)
            sys.exit()

    def add_options(self, vars):
        name = self.name
        upp = name.upper()
        vars.Add(upp + '_DIR', help='Location of %s.'%name)
        vars.Add(upp + '_INC_DIR', help='Location of %s header files.'%name)
        vars.Add(upp + '_LIB_DIR', help='Location of %s libraries.'%name)
        vars.Add(upp + '_LIBS', help='%s libraries.'%name)
        self.options.extend([upp + '_DIR', upp + '_INC_DIR', upp + '_LIB_DIR', upp + '_LIBS'])

    def try_link(self, ctx, **kwargs):
        text = self.get_check_text()
        bkp = env_setup(ctx.env, **kwargs)
        if self.run:
            res = ctx.TryRun(text, self.ext)
        else:
            res = (ctx.TryLink(text, self.ext), '')
        if not res[0]:
            env_restore(ctx.env, bkp)
        return res

    def try_libs(self, ctx, libs, extra_libs=[], **kwargs):
        if not libs:
            libs = [[]]
        if not extra_libs:
            extra_libs = [[]]
        for l in libs:
            l = conv.to_iter(l)
            l_bkp = env_setup(ctx.env, LIBS=l + ctx.env.get('LIBS', []))
            for e in extra_libs:
                e = conv.to_iter(e)
                e_bkp = env_setup(ctx.env, LIBS=ctx.env.get('LIBS', []) + e)
                res = self.try_link(ctx, **kwargs)
                if res[0]:
                    if not self.auto_add_libs:
                        env_restore(ctx.env, e_bkp)
                        env_restore(ctx.env, l_bkp)
                    break
                env_restore(ctx.env, e_bkp)
            if res[0]:
                break
            env_restore(ctx.env, l_bkp)
        return res

    def try_location(self, ctx, base, **kwargs):
        loc_callback = kwargs.get('loc_callback', None)
        libs = copy.deepcopy(conv.to_iter(self.get_libs()))
        extra_libs = copy.deepcopy(conv.to_iter(self.get_extra_libs()))

        sub_dirs = conv.to_iter(self.get_sub_dirs())
        if not sub_dirs:
            sub_dirs = [[]]

        for inc_sub_dirs, lib_sub_dirs in sub_dirs:
            inc_sub_dirs = conv.to_iter(inc_sub_dirs)
            lib_sub_dirs = conv.to_iter(lib_sub_dirs)

            for i in range(len(inc_sub_dirs)):
                if not os.path.isabs(inc_sub_dirs[i]):
                    inc_sub_dirs[i] = os.path.join(base, inc_sub_dirs[i])
            for i in range(len(lib_sub_dirs)):
                if not os.path.isabs(lib_sub_dirs[i]):
                    lib_sub_dirs[i] = os.path.join(base, lib_sub_dirs[i])

            if loc_callback:
                loc_callback(ctx, base, inc_sub_dirs, lib_sub_dirs, libs, extra_libs)

            bkp = env_setup(ctx.env,
                            CPPPATH=ctx.env.get('CPPPATH', []) + inc_sub_dirs,
                            LIBPATH=ctx.env.get('LIBPATH', []) + lib_sub_dirs,
                            RPATH=ctx.env.get('RPATH', []) + lib_sub_dirs)
            res = self.try_libs(ctx, libs, extra_libs, **kwargs)
            if res[0]:
                break
            env_restore(ctx.env, bkp)
        return res

    def get_check_text(self):
        return self.check_text

    def get_libs(self):
        return self.libs

    def get_extra_libs(self):
        return self.extra_libs

    def get_sub_dirs(self):
        return self.sub_dirs

    def have_option(self, env, name):
        if name in env:
            return True
        for opt in self.options:
            if opt in env:
                return False
        return name in env['ENV']

    def have_all_opts(self, env, *names):
        for n in names:
            if not self.have_option(env, n):
                return False
        return True

    def have_any_options(self, env, *names):
        for n in names:
            if self.have_option(env, n):
                return True
        return False

    def get_option(self, env, name):
        if name in env:
            return env[name]
        for opt in self.options:
            if opt in env:
                return ''
        return env['ENV'].get(name, '')

    def check_options(self, env):
        name = self.name.upper()
        if self.have_option(env, name + '_DIR') and self.have_any_options(env, name + '_INC_DIR', name + '_LIB_DIR'):
            print '\n'
            print 'Please pecify either %s_DIR or either of %s_INC_DIR or'%(name, name)
            print '%s_LIB_DIR.\n'%name
            env.Exit()
