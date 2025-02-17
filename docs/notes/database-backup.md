---
title: Apstra Database Backup
description: 
pubDate: 2025-02-15
keywords:
    - Apstra
    - Database
    - Backup
---

## Overview

The procedure for backing up the Apstra database is described in the [Back up Apstra Database](https://www.juniper.net/documentation/us/en/software/apstra5.1/apstra-user-guide/topics/task/apstra-server-database-back-up.html).

The procedure above doesn't mention the way to copy over the database to a remote server, here are the steps to do that.

## Steps to Backup and Transfer Database

### Step 1: Create Database Backup

Login to the Apstra server as admin and take a backup of the database.

```
admin@aos-server:~$ sudo aos_backup
[sudo] password for admin: 
Including secret keys from the backup
Include all sysdb files
====================================================================
  Backup operation completed successfully.
====================================================================
New AOS snapshot: 2025-02-14_23-09-45
admin@aos-server:~$ 
```

{% include note.html content="  " %}
> The name of the snapshot is `2025-02-14_23-09-45` in this example.
> The name of the compressed file is chosen aos-backup-2025-02-14_23-09-45.tgz as example.

### Step 2: Create Compressed Archive

Create a compressed archive of the backup. Note: Replace `snapshot-name` with your actual backup timestamp.

```
admin@aos-server:~$ sudo tar zcf aos-backup-2025-02-14_23-09-45.tgz /var/lib/aos/snapshot/2025-02-14_23-09-45
tar: Removing leading `/' from member names
admin@aos-server:~$ 
```

{% include note.html content="" %}
> The compressed file is created in the admin user home folder - /home/admin.

### Step 3: Set File Permissions

Change the ownership of the backup file.

```
admin@aos-server:~$ sudo chown admin aos-backup-2025-02-14_23-09-45.tgz
```

### Step 4: Transfer the Backup

Choose one of the following methods to transfer the backup file. Replace the IP address and path with your target server details.

#### Option A: Push from Apstra server to remote server

```
scp aos-backup-2025-02-14_23-09-45.tgz fileserver-user@file-server.net:/path/to/the/backup/folder
```

{% include note.html content="" %}
> fix correct fileserver-user, file-server.net, and /path/to/the/backup/folder

#### Option B: Pull from remote server to Apstra server

```
scp admin@apstra-controller.local:/home/admin/aos-backup-2025-02-14_23-09-45.tgz .
```

{% include note.html content="" %}
> fix apstra-controller.local:

#### Option C: Using WinSCP

Use the WinSCP graphical interface to transfer the file. Ensure you have SSH access configured properly.

## Best Practices

- Always verify the backup file size after transfer

```
ls -lh aos-backup-025-02-14_23-09-45.tgz
```

- Keep backups in a secure location
- Consider automating this process for regular backups: [KB37808 Automating Backup Collection](https://supportportal.juniper.net/s/article/Juniper-Apstra-Automating-Backup-Collection)
- Maintain proper backup rotation to manage storage space
- Implement a backup retention policy using a tool like logrotate to automatically delete old backups
