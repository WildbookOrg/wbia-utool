from __future__ import absolute_import, division, print_function
import shelve
#import atexit
import sys
from os.path import join, normpath
from .util_arg import SUPER_STRICT
from . import util_inject
from . import util_hash
from . import util_path
from . import util_io
from . import util_str
from . import util_cplat
from ._internal.meta_util_constants import (global_cache_fname,
                                            global_cache_dname,
                                            default_appname)
print, print_, printDBG, rrr, profile = util_inject.inject(__name__, '[cache]')


# TODO: Remove globalness

VERBOSE = '--verbose' in sys.argv
__SHELF__ = None  # GLOBAL CACHE
__APPNAME__ = default_appname  # the global application name


def text_dict_write(fpath, key, val):
    """
    Very naive, but readable way of storing a dictionary on disk
    """
    try:
        dict_text = util_io.read_from(fpath)
    except IOError:
        dict_text = '{}'
    try:
        dict_ = eval(dict_text)
    except SyntaxError:
        print('Bad Syntax:')
        print(dict_text)
        dict_ = {}
        if SUPER_STRICT:
            raise
    dict_[key] = val
    dict_text2 = util_str.dict_str(dict_, strvals=False)
    if VERBOSE:
        print('[cache] ' + str(dict_text2))
    util_io.write_to(fpath, dict_text2)


def _args2_fpath(dpath, fname, cfgstr, ext, write_hashtbl=False):
    """
    Ensures that the filename is not too long (looking at you windows)
    Windows MAX_PATH=260 characters
    Absolute length is limited to 32,000 characters
    Each filename component is limited to 255 characters

    if write_hashtbl is True, hashed values expaneded and written to a text file
    """
    if len(ext) > 0 and ext[0] != '.':
        raise Exception('Fatal Error: Please be explicit and use a dot in ext')
    fname_cfgstr = fname + cfgstr
    if len(fname_cfgstr) > 128:
        hashed_cfgstr = util_hash.hashstr(cfgstr, 8)
        if write_hashtbl:
            text_dict_write(join(dpath, 'hashtbl.txt'), hashed_cfgstr, cfgstr)
        fname_cfgstr = fname + '_' + hashed_cfgstr
    fpath = join(dpath, fname_cfgstr + ext)
    fpath = normpath(fpath)
    return fpath


def save_cache(dpath, fname, cfgstr, data):
    fpath = _args2_fpath(dpath, fname, cfgstr, '.cPkl', write_hashtbl=True)
    util_io.save_cPkl(fpath, data)


def load_cache(dpath, fname, cfgstr):
    fpath = _args2_fpath(dpath, fname, cfgstr, '.cPkl')
    return util_io.load_cPkl(fpath)


#class Cacher(object):
#    def __init__(self, dpath, fname, cfgstr, text='data'):
#        self.dpath = dpath
#        self.fname = fname
#        self.cfgstr = cfgstr
#        self.data = None
#        self.text = text
#    def tryload(self):
#        try:
#            data = load_cache(self.dpath, self.fname, self.cfgstr)
#            print('... ' + self.text + ' Cacher hit')
#            return data
#        except IOError:
#            print('... ' + self.text + ' Cacher miss')
#    def __exit__(self, type_, value, trace):
#        if trace is not None:
#            print('[util_cache] Error in context manager!: ' + str(value))
#            return False  # return a falsey value on error
#        save_cache(self.dpath, self.fname, self.cfgstr, self.data)


# --- Global Cache ---

def get_global_cache_dir(appname=None, ensure=False):
    """ Returns (usually) writable directory for an application cache """
    if appname is None:
        appname = __APPNAME__
    global_cache_dir = util_cplat.get_app_resource_dir(appname, global_cache_dname)
    if ensure:
        util_path.ensuredir(global_cache_dir)
    return global_cache_dir


def get_global_shelf_fpath(appname=None, ensure=False):
    """ Returns the filepath to the global shelf """
    global_cache_dir = get_global_cache_dir(appname, ensure=ensure)
    shelf_fpath = join(global_cache_dir, global_cache_fname)
    return shelf_fpath


#def get_global_shelf(appname=None):
#    """ Returns the global shelf object """
#    global __SHELF__
#    if __SHELF__ is None:
#        try:
#            shelf_fpath = get_global_shelf_fpath(appname, ensure=True)
#            print(shelf_fpath)
#            __SHELF__ = shelve.open(shelf_fpath)
#        except Exception as ex:
#            from . import util_dbg
#            util_dbg.printex(ex, 'Failed opening shelf_fpath',
#                             key_list=['shelf_fpath'])
#            raise
#        #shelf_file = open(shelf_fpath, 'w')
#    return __SHELF__


#@atexit.register
#def close_global_shelf(appname=None):
#    # FIXME: If the program closes with ctrl+c this isnt called and
#    # the global cache is not written
#    global __SHELF__
#    if __SHELF__ is not None:
#        __SHELF__.close()
#    __SHELF__ = None


class GlobalShelfContext(object):
    def __init__(self, appname):
        self.appname = appname

    def __enter__(self):
        #self.shelf = get_global_shelf(self.appname)
        try:
            shelf_fpath = get_global_shelf_fpath(self.appname, ensure=True)
            if VERBOSE:
                print('[cache] open: ' + shelf_fpath)
            self.shelf = shelve.open(shelf_fpath)
        except Exception as ex:
            from . import util_dbg
            util_dbg.printex(ex, 'Failed opening shelf_fpath',
                             key_list=['shelf_fpath'])
            raise
        return self.shelf

    def __exit__(self, type_, value, trace):
        self.shelf.close()
        if trace is not None:
            print('[util_cache] Error in context manager!: ' + str(value))
            return False  # return a falsey value on error
        #close_global_shelf(self.appname)


def global_cache_read(key, appname=None, **kwargs):
    with GlobalShelfContext(appname) as shelf:
        if 'default' in kwargs:
            return shelf.get(key, kwargs['default'])
        else:
            return shelf[key]


def global_cache_dump(appname=None):
    shelf_fpath = get_global_shelf_fpath(appname)
    print('shelf_fpath = %r' % shelf_fpath)
    with GlobalShelfContext(appname) as shelf:
        print(util_str.dict_str(shelf))


def global_cache_write(key, val, appname=None):
    """ Writes cache files to a safe place in each operating system """
    with GlobalShelfContext(appname) as shelf:
        shelf[key] = val


def delete_global_cache(appname=None):
    """ Reads cache files to a safe place in each operating system """
    #close_global_shelf(appname)
    shelf_fpath = get_global_shelf_fpath(appname)
    util_path.remove_file(shelf_fpath, verbose=True, dryrun=False)
