---
title: Apstra Database Backup
description: 
pubDate: 2025-02-15
keywords:
    - CK-Apstra-API
    - CMS
---

# Apstra Database Backup

## Overview

The procedure for backing up the Apstra database is described in the [Back up Apstra Database](https://www.juniper.net/documentation/us/en/software/apstra5.1/apstra-user-guide/topics/task/apstra-server-database-back-up.html).

As the precude above doesn't mention the way to copy over the database to a remote server, here are the steps to do that.

## Steps to Backup and Transfer Database

### Step 1: Create Database Backup
Login to the Apstra server as admin and take a backup of the database.

```shell
admin@aos-server:~$ sudo aos_backup
[sudo] password for admin: 
Including secret keys from the backup
Include all sysdb files
====================================================================
  Backup operation completed successfully.
====================================================================
New AOS snapshot: <span class="snapshot-name">2025-02-14_23-09-45</span>
admin@aos-server:~$ 
```

### Step 2: Create Compressed Archive
Create a file to be able to copy the database to a remote server.
```
admin@aos-server:~$ sudo tar zcf backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz /var/lib/aos/snapshot/<span class="snapshot-name">2025-02-14_23-09-45</span>
tar: Removing leading `/' from member names
admin@aos-server:~$ 
```

### Step 3: Set File Permissions
Change the ownership of the file to the user that will copy the file to the remote server.
```
admin@aos-server:~$ sudo chown admin backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz
```

### Step 4: Transfer the Backup
This can be done in a number of ways:

#### Option A: Copy from Apstra server to remote server
```
scp backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz admin@10.1.1.100:/home/admin
```

#### Option B: Copy from remote server to Apstra server
```
scp admin@10.1.1.100:/home/admin/backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz .
```

#### Option C: Using WinSCP
Use the WinSCP graphical interface to transfer the file.



