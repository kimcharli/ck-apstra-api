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

<div class="command-block">
admin@aos-server:~$ sudo aos_backup
[sudo] password for admin: 
Including secret keys from the backup
Include all sysdb files
====================================================================
  Backup operation completed successfully.
====================================================================
New AOS snapshot: <span class="snapshot-name">2025-02-14_23-09-45</span>
admin@aos-server:~$ 
</div>

### Step 2: Create Compressed Archive
Create a compressed archive of the backup. Note: Replace <snapshot-name> with your actual backup timestamp.
<div class="command-block">
admin@aos-server:~$ sudo tar zcf aos-backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz /var/lib/aos/snapshot/<span class="snapshot-name">2025-02-14_23-09-45</span>
tar: Removing leading `/' from member names
admin@aos-server:~$ 
</div>

### Step 3: Set File Permissions
Change the ownership of the backup file.
<div class="command-block">
admin@aos-server:~$ sudo chown admin aos-backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz
</div>

### Step 4: Transfer the Backup
Choose one of the following methods to transfer the backup file. Replace the IP address and path with your target server details.

#### Option A: Push from Apstra server to remote server
<div class="command-block">
scp aos-backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz admin@10.1.1.100:/home/admin/
</div>

#### Option B: Pull from remote server to Apstra server
<div class="command-block">
scp admin@aos-server:/home/admin/aos-backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz .
</div>

#### Option C: Using WinSCP
Use the WinSCP graphical interface to transfer the file. Ensure you have SSH access configured properly.

### Best Practices
- Always verify the backup file size after transfer
  <div class="command-block">
  ls -lh aos-backup-<span class="snapshot-name">2025-02-14_23-09-45</span>.tgz
  </div>
- Keep backups in a secure location
- Consider automating this process for regular backups: [KB37808 Automating Backup Collection](https://supportportal.juniper.net/s/article/Juniper-Apstra-Automating-Backup-Collection)
- Maintain proper backup rotation to manage storage space



