# backup.py
## The convenient tarsnap client wrapper

This script offers a convenient interface to the [tarsnap](http://www.tarsnap.com) client. It does not replace it, it just makes certain things more convenient.

### Workflow

1. Create a directory somewhere that contains one directory entry for each archive. Each directory entry may be either a symbolic link or a directory. If it is a directory, it may contain files, symbolic links and subdirectories. You can exclude files within a directory from an archive via the `.backup.py.rc` config file.
2. From time to time (perhaps via a cronjob), you run `backup.py store`, which will create new tarsnap archives by appending the current date (yyyy-mm-dd) to each archive name.

### Getting started

To get started, just run `backup.py store`. You will be told off for not having a `.backup.py.rc`, and one will be created for you. Customize it by setting your directory (the one containing an entry for each archive) and optional exclusions (corresponding to `tarsnap --exclude`), and you're ready to go.

### Other features

Use `backup.py view` to see at which dates each archive was archived.

If an archive is stored twice in a day, you end up with e.g. *foo_2012-03-20* and *foo_2012-03-20.1*.

Use `backup.py list` as a convenient way of saying `tarsnap --list-archives | sort | grep`.

Finally, there's `backup.py rename` which renames an archive (this operates on the remote archives with their full names, including the date suffix).

