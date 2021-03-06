import os, sys, copy, shutil, subprocess, shlex
import sconsconfig.utils as utils
from sconsconfig.utils import conv
from SCons.Variables import BoolVariable

## Backup a list of environment variables.
#  @param[in] env An SCons environment.
#  @param[in] names A list of environment names to backup.
#  @returns A dictionary of backed up names and values.
def env_backup(env, names):
    names = conv.to_iter(names)
    bkp = {}
    for n in names:
        if n not in env:
            bkp[n] = None
        else:
            bkp[n] = env[n]
    return bkp

## Backup the existing environment and update with provided keywords.
#  @see env_backup
#  @param[in] env An SCons environment.
#  @returns A dictionary of backed up names and values.
def env_setup(env, **kw):
    bkp = env_backup(env, kw.keys())
    env.Replace(**kw)
    return bkp

## Restore a set of previously backed up environment macros.
#  @see env_backup
#  @param[in] env An SCons environment.
#  @param[in] bkp A dictionary of backed up key/values returned by env_backup.
def env_restore(env, bkp):
    '''
    '''
    for n, v in bkp.iteritems():
        if v is None:
            del env[n]
        else:
            env[n] = v

## Base class for all configuration packages.
class Package(object):

    ## Default include/library sub-directories to search.
    DEFAULT_SUB_DIRS = [('include', 'lib'), ('include', 'lib64')]

    ##
    #  @param[in] required Boolean indicating whether the configuration should fail if this package
    #                      cannot be found.
    #  @param[in] download_url Location to download the package if required.
    def __init__(self, required=True, download_url=''):
        self.name = self.__class__.__name__
        self.required = required
        self.found = False
        self.headers = []
        self.libs = []
        self.extra_libs = []
        self.sub_dirs = self.DEFAULT_SUB_DIRS
        self.check_text = ''
        self.options = []
        self.one_shot_options = []
        self.test_names = ['Check' + self.name]
        self.custom_tests = {'Check' + self.name: self.check}
        self.auto_add_libs=True
        self.run=True
        self.ext = '.c'
        self.download_url = download_url
        self.build_handlers = {}

        self.base_dir = None
        self._used_inc_dirs = None
        self._used_libs = None

    ##
    #  TODO: Make more general
    def include_directories(self):
        return os.path.join(self.base_dir, 'include')

    ##
    #  TODO: This needs to be more general.
    def libraries(self):
        if self._used_libs:
            return os.path.join(self.base_dir, 'lib', 'lib' + self._used_libs[0] + '.so')
        else:
            return ''

    ## Run the configuration checks for this package.
    #  @param[in,out] ctx The configuration context, retrieved from SCons.
    def check(self, ctx, **kwargs):
        ctx.Log('Beginning check for %s\n'%self.name)
        env = ctx.env
        name = self.name
        libs = self.libs
        extra_libs = self.extra_libs
        sub_dirs = self.sub_dirs

        upp = name.upper()
        if self.have_option(env, upp + '_DIR'):
            value = self.get_option(env, upp + '_DIR')
            ctx.Log('Found option %s = %s\n'%(upp + '_DIR', value))
            res = self.try_location(ctx, value, **kwargs)
            if not res[0]:
                self._msg = '\n\nUnable to find a valid %s installation at:\n  %s\n'%(name, value)
                # ctx.Log(msg)
                # print msg
                # env.Exit(1)

        elif self.have_any_options(env, upp + '_INC_DIR', upp + '_LIB_DIR', upp + '_LIBS'):
            inc_dirs = self.get_option(env, upp + '_INC_DIR').split(';')
            lib_dirs = self.get_option(env, upp + '_LIB_DIR').split(';')
            if self.have_option(env, upp + '_LIBS'):
                cur_libs = [map(env.File, self.get_option(env, upp + '_LIBS').split(';'))]
                cur_extra_libs = []
            else:
                cur_libs = libs
                cur_extra_libs = extra_libs
            ctx.Log('Found options:\n')
            if inc_dirs:
                kwargs['inc_dirs'] = inc_dirs
                ctx.Log('  %s = %s\n'%(upp + '_INC_DIR', str(inc_dirs)))
            if lib_dirs:
                kwargs['lib_dirs'] = lib_dirs
                ctx.Log('  %s = %s\n'%(upp + '_LIB_DIR', str(lib_dirs)))
            if self.have_option(env, upp + '_LIBS'):
                kwargs['libs'] = cur_libs
                kwargs['extra_libs'] = []
                ctx.Log('  %s = %s\n'%(upp + '_LIBS', str([l.path for l in cur_libs])))

            res = (True, 0)
            if inc_dirs:
                if not self.try_headers(ctx, inc_dirs):
                    res = (False, 0)
            bkp = env_setup(ctx.env,
                            CPPPATH=ctx.env.get('CPPPATH', []) + inc_dirs,
                            LIBPATH=ctx.env.get('LIBPATH', []) + lib_dirs,
                            RPATH=ctx.env.get('RPATH', []) + lib_dirs)
            if res[0]:
                res = self.try_libs(ctx, libs, **kwargs)
            if not res[0]:
                env_restore(ctx.env, bkp)
                self._msg = '\n\nUnable to find a valid %s installation using:\n'%name
                if self.have_option(env, upp + '_INC_DIR'):
                    self._msg += '  Header directories: %s\n'%str(inc_dirs)
                if self.have_option(env, upp + '_LIB_DIR'):
                    self._msg += '  Library directories: %s\n'%str(lib_dirs)
                if self.have_option(env, upp + '_LIBS'):
                    self._msg += '  Libraries: %s\n'%str([l.path for l in cur_libs])
                # ctx.Log(msg)
                # print msg
                # env.Exit(1)

        # Check if the user requested to download this package.
        elif self.have_any_options(env, upp + '_DOWNLOAD', 'DOWNLOAD_ALL') and self.download_url:

            # Perform the auto-management of this package.
            res = self.auto(ctx)

            # For now we assume a package location is set entirely with <NAME>_DIR.
            if res[0]:
                value = self.get_option(env, upp + '_DIR')
                res = self.try_location(ctx, value, **kwargs)
                if not res[0]:
                    self._msg = '\n\nUnable to find a valid %s installation at:\n  %s\n'%(name, value)
                    # ctx.Log(msg)
                    # print msg
                    # env.Exit(1)

        else:
            ctx.Log('No options found, trying empty location.\n')
            res = self.try_libs(ctx, libs, extra_libs, **kwargs)

            if not res[0]:
                ctx.Log('Trying common locations.\n')
                common_dirs = ['/usr/local', os.environ['HOME'], os.path.join(os.environ['HOME'], 'soft'), '/sw']
                res = (0, '')
                for cd in common_dirs:
                    if not os.path.exists(cd):
                        ctx.Log('%s does not exist.\n'%cd)
                        continue
                    ctx.Log('Looking in %s\n'%cd)
                    for d in os.listdir(cd):
                        if d.find(name) == -1 and d.find(name.lower()) == -1 and d.find(name.upper()) == -1:
                            continue
                        d = os.path.join(cd, d)
                        if not os.path.isdir(d):
                            ctx.Log('%s is not a directory.\n')
                            continue
                        res = self.try_location(ctx, d, **kwargs)
                        if res[0]:
                            break
                    if res[0]:
                        break

                if res[0]:
                    env[upp + '_DIR'] = d

        return res

    def check_required(self, result, ctx=None):
        name = self.name
        upp = name.upper()

        # Stash the result.
        self.found = bool(result)

        # Failed specified location?
        if not result and hasattr(self, '_msg') and self.required:
            ctx.Log(self._msg)
            print self._msg
            sys.exit(1)

        # General failure?
        if not result and self.required:
            print '\n'
            print 'Unable to locate required package %s. You can specify'%name
            print 'the location using %s_DIR or a combination of'%upp
            print '%s_INC_DIR, %s_LIB_DIR and %s_LIBS.'%(upp, upp, upp)
            print 'You can also specify %s_DOWNLOAD to'%upp
            print 'automatically download and install the package.\n'
            sys.exit(1)

        # If the package is not required but was found anyway, add a preprocessor
        # flag indicating such.
        elif result:
            if ctx and not self.required:
                ctx.env.AppendUnique(CPPDEFINES=['HAVE_' + upp])

    def add_options(self, vars):
        name = self.name
        upp = name.upper()
        vars.Add(upp + '_DIR', help='Location of %s.'%name)
        vars.Add(upp + '_INC_DIR', help='Location of %s header files.'%name)
        vars.Add(upp + '_LIB_DIR', help='Location of %s libraries.'%name)
        vars.Add(upp + '_LIBS', help='%s libraries.'%name)
        if self.download_url:
            vars.Add(BoolVariable(upp + '_DOWNLOAD', help='Download and use a local copy of %s.'%name, default=False))
            vars.Add(BoolVariable(upp + '_REDOWNLOAD', help='Force update of previously downloaded copy of %s.'%name, default=False))
            self.one_shot_options.append(upp + '_REDOWNLOAD')
        self.options.extend([upp + '_DIR', upp + '_INC_DIR', upp + '_LIB_DIR', upp + '_LIBS', upp + '_DOWNLOAD'])

    ## Set the build handler for an architecture and operating system. Pass in None to the handler
    #  to clear the current handler.
    #  @param[in] handler The handler string to use.
    #  @param[in] sys_id The kind of system to set for.
    def set_build_handler(self, handler, sys_id=None):
        if handler is None and sys_id in self.build_handlers:
            del self.build_handlers[sys_id]
        else:
            self.build_handlers[sys_id] = handler

    def get_build_handler(self):
        import platform
        os = platform.system()
        arch = platform.architecture()[0]
        sys_id = os + '_' + arch
        if sys_id in self.build_handlers:
            return self.build_handlers[sys_id]
        if os in self.build_handlers:
            return self.build_handlers[os]
        if arch in self.build_handlers:
            return self.build_handlers[arch]
        return self.build_handlers.get(None, None)

    def auto(self, ctx):
        sys.stdout.write('\n')

        # Are we forcing this?
        upp = self.name.upper()
        force = self.have_option(ctx.env, upp + '_REDOWNLOAD')

        # Create the source directory if it does not already exist.
        src_dir = os.path.join('external_packages', 'src')
        if not os.path.exists(src_dir):
            os.makedirs(src_dir)
        ctx.Log("Downloading into " + src_dir + "\n")

        # Setup the filename and build directory name and distination directory.
        filename = self.name + self.download_url[self.download_url.rfind('/') + 1:]
        build_dir = self.name.lower()
        dst_dir = os.path.abspath(os.path.join('external_packages', self.name.lower()))
        ctx.Log("Building into " + dst_dir + "\n")

        # Change to the source directory.
        old_dir = os.getcwd()
        os.chdir(src_dir)

        # Download if the file is not already available.
        if not os.path.exists(filename) or force:
            if not self.auto_download(ctx, filename):
                os.chdir(old_dir)
                return (0, '')

        # Unpack if there is not already a build directory by the same name.
        if not os.path.exists(build_dir) or force:
            if not self.auto_unpack(ctx, filename, build_dir):
                os.chdir(old_dir)
                return (0, '')

        # Move into the build directory. Most archives will place themselves
        # in a single directory which we should then move into.
        os.chdir(build_dir)
        entries = os.listdir('.')
        if len(entries) == 1:
            os.chdir(entries[0])

        # Build the package.
        if not os.path.exists('scons_build_success') or force:
            if not self.auto_build(ctx, dst_dir):
                os.chdir(old_dir)
                return (0, '')

        # Set the directory location.
        ctx.env[self.name.upper() + '_DIR'] = dst_dir

        sys.stdout.write('  Configuring with downloaded package ... ')
        os.chdir(old_dir)
        return (1, '')

    def auto_download(self, ctx, filename):
        sys.stdout.write('  Downloading ... ')
        sys.stdout.flush()

        if os.path.exists(filename):
            os.remove(filename)

        ctx.Log("Downloading file from " + self.download_url + "\n")
        try:
            import urllib
            urllib.urlretrieve(self.download_url, filename)
            sys.stdout.write('done.\n')
            return True
        except:
            sys.stdout.write('failed.\n')
            ctx.Log("Failed to download file\n")
            return False

    def auto_unpack(self, ctx, filename, build_dir):
        sys.stdout.write('  Extracting ... ')
        sys.stdout.flush()

        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

        # TODO: DRY
        ctx.Log("Extracting contents of " + filename + "\n")
        if os.path.splitext(filename)[1] == '.zip':
            ctx.Log("Using zip\n")
            try:
                import zipfile
                zf = zipfile.ZipFile(filename)
                zf.extractall(build_dir)
                zf.close()
            except:
                shutil.rmtree(build_dir, True)
                sys.stdout.write('failed.\n')
                ctx.Log("Failed to extract file\n")
                return False
        else:
            ctx.Log("Using tar\n")
            try:
                import tarfile
                tf = tarfile.open(filename)
                tf.extractall(build_dir)
            except:
                shutil.rmtree(build_dir, True)
                sys.stdout.write('failed.\n')
                ctx.Log("Failed to extract file\n")
                return False

        # If there is a patch, try to patch code.
        patch = os.path.join(utils.get_data_prefix(), 'patches', self.name.lower() + '.patch')
        if os.path.exists(patch):
            ctx.Log('Trying to apply patch.')
            try:
                utils.apply_patch(build_dir, patch)
            except:
                shutil.rmtree(build_dir, True)
                ctx.Log('failed to apply patch\n')
                return False

        sys.stdout.write('done.\n')
        return True

    def auto_build(self, ctx, dst_dir):
        sys.stdout.write('  Building package, this could take a while ... ')
        sys.stdout.flush()
        ctx.Log("Building package in " + dst_dir + "\n")

        # Remove any existing file used to indicate successful builds.
        import os
        if os.path.exists('scons_build_success'):
            os.remove('scons_build_success')

        # Remove the installation directory.
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        # Hunt down the correct build handler.
        handler = self.get_build_handler()
        if handler is None:
            sys.stdout.write('failed.\n  Sorry, this system/architecture is not supported.\n')
            ctx.Log("Failed to locate build handler\n")
            return False

        # Make a file to log stdout from the commands.
        stdout_log = open('stdout.log', 'w')

        # Process each command in turn.
        for cmd in handler:

            # It's possible to have a tuple, indicating a function and arguments.
            if isinstance(cmd, tuple):
                ctx.Log("Command is a Python function\n")
                func = cmd[0]
                args = cmd[1:]

                # Perform substitutions.
                args = [ctx.env.subst(a.replace('${PREFIX}', dst_dir)) for a in args]

                # Call the function.
                func(*args)

            else:

                # If the first character in a command is an "!", then it means we allow
                # errors from this command.
                allow_errors = False
                if cmd[0] == '!':
                    allow_errors = True
                    cmd = cmd[1:]

                # Perform substitutions.
                cmd = cmd.replace('${PREFIX}', dst_dir)
                cmd = ctx.env.subst(cmd)
                ctx.Log(cmd + "\n")

                try:
                    subprocess.check_call(shlex.split(cmd), stdout=stdout_log, stderr=subprocess.STDOUT)
                except:
                    if not allow_errors:
                        stdout_log.close()
                        sys.stdout.write('failed.\n')
                        ctx.Log("Command failed\n")
                        return False

        # Don't forget to close the log.
        stdout_log.close()

        # If it all seemed to work, write a dummy file to indicate this package has been built.
        success = open('scons_build_success', 'w')
        success.write(' ')
        success.close()

        sys.stdout.write('done.\n')
        return True

    def env_setup_libs(self, env, libs):
        defaults = {
            'prepend': True,
            'libraries': libs,
        }

        # If we were given a dictionary update our defaults.
        if len(libs) and isinstance(libs[0], dict):
            defaults.update(libs[0])
            defaults['libraries'] = conv.to_iter(defaults['libraries'])

        # Remove any pre-existing libraries.
        defaults['libraries'] = [d for d in defaults['libraries'] if d not in env.get('LIBS', [])]

        # Prepend or append?
        if defaults['prepend']:
            libs = defaults['libraries'] + conv.to_iter(env.get('LIBS', []))
        else:
            libs = conv.to_iter(env.get('LIBS', [])) + defaults['libraries']

        return env_setup(env, LIBS=libs)

    def try_link(self, ctx, **kwargs):
        text = self.check_text
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
            l_bkp = self.env_setup_libs(ctx.env, l)
            for e in extra_libs:
                e = conv.to_iter(e)
                e_bkp = env_setup(ctx.env, LIBS=ctx.env.get('LIBS', []) + e)
                res = self.try_link(ctx, **kwargs)
                if res[0]:
                    if not self.auto_add_libs:
                        env_restore(ctx.env, e_bkp)
                        env_restore(ctx.env, l_bkp)
                    self._used_libs = l
                    break
                env_restore(ctx.env, e_bkp)
            if res[0]:
                break
            env_restore(ctx.env, l_bkp)
        return res

    def try_headers(self, ctx, inc_dirs, **kwargs):
        ctx.Log('Trying to find headers in %s\n'%repr(inc_dirs))
        found_headers = True
        for hdr in self.headers:
            found = False
            for path in inc_dirs:
                hdr_path = os.path.join(path, hdr)
                ctx.Log('  ' + hdr_path + ' ... ')
                if os.path.exists(hdr_path):
                    ctx.Log('yes.\n')
                    found = True
                    break
                ctx.Log('no.\n')
            if not found:
                ctx.Log('Failed to find ' + hdr + '\n')
                found_headers = False
                break
        return found_headers

    def try_location(self, ctx, base, **kwargs):
        ctx.Log('Checking for %s in %s.\n'%(self.name, base))
        loc_callback = kwargs.get('loc_callback', None)
        libs = copy.deepcopy(conv.to_iter(self.libs))
        extra_libs = copy.deepcopy(conv.to_iter(self.extra_libs))

        sub_dirs = conv.to_iter(self.sub_dirs)
        if not sub_dirs:
            sub_dirs = [[]]

        res = (False, None)
        for inc_sub_dirs, lib_sub_dirs in sub_dirs:
            inc_sub_dirs = list(conv.to_iter(inc_sub_dirs))
            lib_sub_dirs = list(conv.to_iter(lib_sub_dirs))

            for i in range(len(inc_sub_dirs)):
                if not os.path.isabs(inc_sub_dirs[i]):
                    inc_sub_dirs[i] = os.path.join(base, inc_sub_dirs[i])
            for i in range(len(lib_sub_dirs)):
                if not os.path.isabs(lib_sub_dirs[i]):
                    lib_sub_dirs[i] = os.path.join(base, lib_sub_dirs[i])

            # Remove any directories that can already be found in
            # in their respective lists.
            inc_sub_dirs = [d for d in inc_sub_dirs if d not in ctx.env.get('CPPPATH', [])]
            lib_sub_dirs = [d for d in lib_sub_dirs if d not in ctx.env.get('LIBPATH', [])]

            if loc_callback:
                loc_callback(ctx, base, inc_sub_dirs, lib_sub_dirs, libs, extra_libs)

            ctx.Log('Trying include dirs: ' + str(inc_sub_dirs) + '\n')
            ctx.Log('Trying library dirs: ' + str(lib_sub_dirs) + '\n')

            # Before continuing, try and find all of the sample headers.
            if not self.try_headers(ctx, inc_sub_dirs, **kwargs):
                continue

            bkp = env_setup(ctx.env,
                            CPPPATH=ctx.env.get('CPPPATH', []) + inc_sub_dirs,
                            LIBPATH=ctx.env.get('LIBPATH', []) + lib_sub_dirs,
                            RPATH=ctx.env.get('RPATH', []) + lib_sub_dirs)
            res = self.try_libs(ctx, libs, extra_libs, **kwargs)
            if res[0]:
                self.base_dir = base # set base directory
                break
            env_restore(ctx.env, bkp)
        return res

    def have_option(self, env, name):
        if name in env and env[name] is not False:
            return True

        # Only check the OS environment if no other options for this package were given.
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

        # Either base or include/library paths.
        if self.have_option(env, name + '_DIR') and self.have_any_options(env, name + '_INC_DIR', name + '_LIB_DIR'):
            print '\n'
            print 'Please pecify either %s_DIR or either of %s_INC_DIR or'%(name, name)
            print '%s_LIB_DIR.\n'%name
            env.Exit(1)

        # Either download or location.
        elif self.have_option(env, name + '_DOWNLOAD') and self.have_any_options(env, name + '_DIR', name + '_INC_DIR', name + '_LIB_DIR'):
            print '\n'
            print 'Cannot specify to download %s and also give a system location.'%self.name
            env.Exit(1)

    def need_cmake(self, env):
        if not self.have_cmake():
            print '\n'
            print '%s requires CMake to be installed to autobuild.'%self.name
            print
            env.Exit(1)

    def have_cmake(self):
        if getattr(self, '_cmake', False):
            return self._cmake
        try:
            subprocess.check_call('cmake', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._cmake = True
        except:
            self._cmake = False
        return self._cmake
