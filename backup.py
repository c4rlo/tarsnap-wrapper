#!/usr/bin/python3

# TODO:
# - Delete old archives?


import argparse, sys, subprocess, os, os.path, datetime, re, configparser
from collections import defaultdict
from itertools import count
from operator import itemgetter


# Global variables (from config)

top_dir = None
exclusions = None


# Commands

def store():
    os.chdir(top_dir)

    if len(args.archives) == 0:
        entries = os.listdir(top_dir)
        abs_paths = [ os.path.join(top_dir, entry) for entry in entries ]

        du_process = subprocess.Popen(['du', '-Lbs'] + abs_paths, stdout=subprocess.PIPE)
        du_so, du_se = du_process.communicate()
        entry_sizes = [ line.split('\t') for line in du_so.decode().rstrip('\n').split('\n') ]
        assert len(entry_sizes) == len(entries)
        item_to_size = { os.path.basename(es[1]): int(es[0]) for es in entry_sizes }

        for item in sorted(entries, key = lambda e: item_to_size[e]):
            store_single(item)
    else:
        for item in args.archives:
            if not os.path.exists(item):
                sys.exit("{} does not exist in {}".format(item, top_dir))
            store_single(item)

    log("Done")

def view():
    archives = defaultdict(set)
    re_ls_line = re.compile(r'(.*)_(\d\d\d\d-\d\d-\d\d(?:\.\d+)?)$')
    for line in do_list():
        m = re_ls_line.match(line)
        if m:
            name, suffix = m.groups()
            archives[name].add(suffix)
        else:
            archives[line].add('(no suffix)')
    for name, suffixes in sorted(archives.items(), key=itemgetter(0)):
        if suffixes == { '(no suffix)' }:
            print(name)
        else:
            suf = '\n'.join([ '\t' + s for s in sorted(suffixes) ])
            print('{}:\n{}\n'.format(name, suf))

def rename():
    try:
        subprocess.check_call(('tarsnap', '-cf', args.new, '@@' + args.old))
        subprocess.call(('tarsnap', '-df', args.old))
    except subprocess.CalledProcessError: pass

def list_archives():
    if args.substring is None:
        ls = do_list()
    else:
        ls = (a for a in do_list() if args.substring in a)
    for ar in sorted(ls):
        print(ar)


# Helpers

def do_list():
    try:
        proc = subprocess.Popen(('tarsnap', '--list-archives'),
                              stdout=subprocess.PIPE)
        done = False
        for line in proc.stdout:
            yield line.decode().rstrip('\n')
        done = True
    finally:
        if not done:
            for line in proc.stdout: pass
        proc.stdout.close()
        status = proc.wait()
        if done and status != 0:
            sys.exit(status)

def store_single(archive):
    today_str = datetime.date.today().isoformat()
    arch_name = archive + '_' + today_str
    log("Archiving {}...".format(archive))
    tarsnap_cmd = [ 'tarsnap', '-L' ]
    for exclusion in exclusions.get(archive, ()):
        tarsnap_cmd.extend([ '--exclude', os.path.join(archive, exclusion) ])
    arch_name_try = arch_name
    for numtry in count(1):
        create_cmd = tarsnap_cmd + [ '-cf', arch_name_try, archive ]
        tarsnap = subprocess.Popen(create_cmd, stderr=subprocess.PIPE)
        tarsnap_so, tarsnap_se = tarsnap.communicate()
        tarsnap_se = tarsnap_se.decode()
        if tarsnap.returncode == 0:
            sys.stderr.write(tarsnap_se)
            return
        elif 'archive already exists' in tarsnap_se:
            arch_name_try = "{}.{}".format(arch_name, numtry)
        else:
            sys.exit(tarsnap_se)

def log(msg):
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    print("\n{} {}".format(now_str, msg))


# Config parsing

sample_cfg = \
'''# tarsnap backup.py configuration file

[General]
# The directory which contains archives as directories or symbolic links
# (mandatory)
# directory = /home/carlo/tarsnap/links

# An example exclusion section: within archive "firefox-profile",
#   exclude the listed items.  The tarsnap --exclude feature is used.

# [exclusions firefox-profile]
# Cache
# urlclassifier2
# urlclassifier3
'''

def parse_config():
    filename = os.path.join(os.environ['HOME'], '.backup.py.rc')
    if not os.path.isfile(filename):
        sys.stderr.write(
            "Configuration file " + filename + " not found.\n")
        try:
            with open(filename, 'w') as f: f.write(sample_cfg)
            sys.exit("Created a sample .backup.py.rc, please customize.")
        except IOError as e:
            sys.exit("Failed to create a sample file: {}".format(e))

    config = configparser.ConfigParser(allow_no_value = True)
    config.optionxform = str  # option names should be case-sensitive

    try:
        config.read(filename)
    except configparser.ParsingError as e:
        sys.exit("Error parsing {}: {}".format(filename, e))

    global top_dir, exclusions

    try:
        top_dir = config['General']['directory']
    except KeyError:
        sys.exit(filename + " is missing a 'directory' entry")

    exclusions = { }
    excl_re = re.compile(r'exclusions (.+)')
    for name, section in config.items():
        if name in ('DEFAULT', 'General'): continue
        excl_match = excl_re.match(name)
        if excl_match:
            arch = excl_match.group(1)
            exclusions[arch] = list(section.keys())
        else:
            sys.exit("unexpected section name: " + name)


# Argument parsing

def parse_args():
    argParser = argparse.ArgumentParser(description='tarsnap backup wrapper')
    subparsers = argParser.add_subparsers(title='subcommands', dest='subcommand')

    storeParser = subparsers.add_parser('store', help='make a new backup',
                                        description='''\
    Make a new backup. The archive names must exist as directories or symlinks
    under {0}. The current date in ISO format will be appended (e.g.
    foo_2012-03-20); if that name already exists on the server, an integer is
    appended (e.g.  foo_2012-03-20.1). If no archives are given, all under {0}
    are processed, in ascending order of size on local storage.\
                                        '''.format(top_dir))
    storeParser.set_defaults(func=store)
    storeParser.add_argument('archives', metavar='archive', nargs='*',
                             help='archive name')

    viewParser = subparsers.add_parser('view', help='view current backups',
                                       description='''\
    View remote archives, grouped by name. For each name, the set of date
    suffixes is shown. See also the 'list' subcommand.''')
    viewParser.set_defaults(func=view)

    moveParser = subparsers.add_parser('rename', help='rename tarsnap archive',
                                       description='''\
    Rename remote archive. Both 'old' and 'new' must refer to the full name,
    such as 'foo_2012-03-20.1'.''')
    moveParser.set_defaults(func=rename)
    moveParser.add_argument('old', help='old archive name')
    moveParser.add_argument('new', help='new archive name')

    listParser = subparsers.add_parser('list', help='list archives',
                                       description='''\
    List remote archives. Unlike the 'view' subcommand, this does not group the
    archives by name; date suffixes are included. Archives are sorted by full
    name.  A substring may be provided for which to grep.''')
    listParser.set_defaults(func=list_archives)
    listParser.add_argument('substring', nargs='?',
                            help='the substring to match (optional)')

    return argParser.parse_args()


# Main

parse_config()
args = parse_args()
args.func()
