Remote Rsync script
==========================================

* Author:    Javier Romero (<jrgn@kth.se>)
* GitHub:    <https://github.com/libicocco/Hand>

This free software is copyleft licensed under version 3 of the GPL license.

The goal of this script is to perform a rotary backup in a remote server.
Suitable for running regularly with cron.

Usage:
------

You should have ssh access to the server where you want to backup to.
Create an ssh key pair:

    user@local-host$ [Note: You are on local-host here]
    user@local-host$ ssh-keygen
    Generating public/private rsa key pair.
    Enter file in which to save the key (/home/user/.ssh/id_rsa):[Enter path, like /home/user/.ssh/remote_rsync_id_rsa]
    Enter passphrase (empty for no passphrase): [Press enter key]
    Enter same passphrase again: [Pess enter key]
    Your identification has been saved in /home/user/.ssh/remote_rsync_id_rsa.
    Your public key has been saved in /home/user/.ssh/remote_rsync_id_rsa.pub.
    The key fingerprint is:
    45:b5:ae:ab:95:95:18:11:51:d5:dc:96:2a:a2:55:a9 

And copy it to the server:

    user@local-host$ ssh-copy-id -i ~/.ssh/remote_rsync_id_rsa.pub user@remote-host

Now you can backup your data by specifying the server, the data to be backed up and the ssh private key:
    
    python3 remote_rsync.py  -s user@remote-host -d /home/user/ -k /home/user/.ssh/remote_rsync_id_rsa

You can create excluding rules by using the file backup_exclude (read the provided file for an example on how to use it) or creating a file named .nobackup in the folders not to be backed up

Contributors:
-------------

* Javier Romero [1]

[1]: https://github.com/libicocco
