#!/usr/bin/python3

TOP_DIR = '/home/carlo/tarsnap/links'
EXCLUSIONS = {
    'firefox-profile': (
        'Cache',
        'urlclassifier3.sqlite',
        'urlclassifier2.sqlite',
    )
}

# TODO:
# - Delete old archives?

import argparse, sys, subprocess, os, os.path, datetime, re
from collections import defaultdict


# Helpers

def log(msg):
    now_str = datetime.datetime.now().strftime('%H:%M:%S')
    print("\n{} {}".format(now_str, msg))

def do_list():
    return subprocess.check_output(('tarsnap', '--list-archives')).decode(). \
            rstrip('\n').split('\n')

def store_single(archive):
    today_str = datetime.date.today().isoformat()
    arch_name = archive + '_' + today_str
    log("Archiving {}...".format(archive))
    create_cmd = [ 'tarsnap', '-L' ]
    for exclusion in EXCLUSIONS.get(archive, ()):
        create_cmd.extend([ '--exclude', os.path.join(archive, exclusion) ])
    create_cmd.extend([ '-cf', arch_name, archive ])
    if args.force:
        tarsnap = subprocess.Popen(create_cmd, stderr=subprocess.PIPE)
        tarsnap_so, tarsnap_se = tarsnap.communicate()
        if tarsnap.returncode != 0:
            tarsnap_se = tarsnap_se.decode()
            if 'archive already exists' in tarsnap_se:
                subprocess.check_call(('tarsnap', '-df', arch_name))
                subprocess.call(create_cmd)
            else:
                sys.exit(tarsnap_se)
    else:
        subprocess.call(create_cmd)


# Commands

def store():
    os.chdir(TOP_DIR)

    if len(args.archives) == 0:
        entries = os.listdir(TOP_DIR)
        abs_paths = [ os.path.join(TOP_DIR, entry) for entry in entries ]

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
                sys.exit("{} does not exist in {}".format(item, TOP_DIR))
            store_single(item)

    log("Done")

def view():
    archives = defaultdict(set)
    re_ls_line = re.compile(r'(.*)_(\d\d\d\d-\d\d-\d\d)$')
    for line in do_list():
        m = re_ls_line.match(line)
        if m:
            name, date = m.groups()
            archives[name].add(date)
        else:
            archives[line] = set()
    for k in sorted(archives.keys()):
        value = archives[k]
        if len(value) > 0:
            dates_str = ''.join([ '\t' + d + '\n' for d in sorted(value) ])
            print("{}:\n{}".format(k, dates_str))
        else:
            print(k)

def rename():
    try:
        subprocess.check_call(('tarsnap', '-cf', args.new, '@@' + args.old))
        subprocess.call(('tarsnap', '-df', args.old))
    except subprocess.CalledProcessError: pass

def list_archives():
    for ar in sorted(do_list()):
        if args.substring is None or args.substring in ar:
            print(ar)


# Argument parsing

argParser = argparse.ArgumentParser(description='tarsnap backup wrapper')
subparsers = argParser.add_subparsers(title='subcommands', dest='subcmd',
                                      help='default is store')

storeParser = subparsers.add_parser('store', help='make a new backup',
                                    description='make a new backup')
storeParser.set_defaults(func=store)
storeParser.add_argument('archives', metavar='archive', nargs='*',
                         help='archive name (without date suffix); \
                         if none given, default to all')
storeParser.add_argument('-f', '--force', action='store_true',
                         help='overwrite existing archives')

viewParser = subparsers.add_parser('view', help='view current backups',
                                   description='view current backups')
viewParser.set_defaults(func=view)

moveParser = subparsers.add_parser('rename', help='rename tarsnap archive',
                                   description='rename tarsnap archive')
moveParser.set_defaults(func=rename)
moveParser.add_argument('old', help='old archive name')
moveParser.add_argument('new', help='new archive name')

listParser = subparsers.add_parser('list', help='list archives',
                                   description='list archives matching optional pattern')
listParser.set_defaults(func=list_archives)
listParser.add_argument('substring', nargs='?',
                        help='the substring to match (optional)')

args = argParser.parse_args()
args.func()
