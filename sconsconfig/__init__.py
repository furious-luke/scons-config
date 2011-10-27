from utils import conv
import packages

enabled_packages = []
custom_tests = {}

def select(*args):
    packages = args
    for pkg in packages:
        if pkg in enabled_packages:
            continue
        enabled_packages.append(pkg)
        custom_tests.update(pkg.custom_tests)

def add_options(vars):
    for pkg in enabled_packages:
        pkg.add_options(vars)

def check(sconf):
    for pkg in enabled_packages:
        for name in conv.to_iter(pkg.test_names):
            getattr(sconf, name)()

def configure(env):
    sconf = env.Configure(custom_tests=custom_tests)
    check(sconf)
    sconf.Finish()
