# backup.py
## The convenient tarsnap client wrapper

This script offers a convenient interface to the *tarsnap* client.

The assumed workflow is:
1. You create a directory somewhere that contains one directory entry for each archive. Each directory entry may be either a symbolic link or a directory. If it is a directory, it may contain files, symbolic links and subdirectories.
2. From time to time (perhaps via a cronjob), you run `backup.py store`, which will create new tarsnap archives by appending the current date (yyyy-mm-dd) to each archive name.

Use `backup.py view` to see at which dates each archive was archived.

Use `backup.py store -f` to overwrite existing archives (necessary if you want to archive the same archive twice in a day).

Use `backup.py list` as a convenient way of saying `tarsnap --list-archives | sort | grep`.

Finally, there's `backup.py rename` which renames an archive (this operates on the remote archives with its full name, including the date suffix).

To get started, just run `backup.py store`. You will be told off for not having a `.backup.py.rc`, and one will be created for you. Customize it by setting your directory (the ony containing an entry for each archive) and optional exclusions (corresponding to `tarsnap --exclude`), and you're ready to go.
