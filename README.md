# vm-facts

This role parses the existing `hostvars` of VMs and generates vars used by [xen_vman](https://github.com/stuvusIT/xen_vman), [zfs-storage](https://github.com/stuvusIT/zfs-storage/), [zfs-snap-manager](https://github.com/stuvusIT/zfs-snap-manager/), [zfs-auto-snapshot](https://github.com/stuvusit/zfs-auto-snapshot) and [iscsi-target](https://github.com/stuvusIT/iscsi-target/).
With correct vars set, this role is able to gather and set all facts needed to create ZFS filesystems/ZVOLs, share them via NFS or iSCSI, snapshot them (locally and for remote replication) and configure XEN instances for them.

## Requirements

A Linux distribution.

## Role Variables

| Name                                 | Default / Mandatory      | Description                                                                                          |
|:-------------------------------------|:------------------------:|:-----------------------------------------------------------------------------------------------------|
| `vm_facts_generate_storage_facts`    | `False`                  | Flag to activate fact generation for storage variables (ZFS, NFS, iSCSI).                            |
| `vm_facts_generate_backup_facts`     | `False`                  | Flag to activate fact generation for storage variables (ZFS).                                        |
| `vm_facts_generate_hypervisor_facts` | `False`                  | Flag to activate fact generation for hypervisor variables (Xen).                                     |
| `vm_facts_default_hypervisor_host`   | :heavy_check_mark:       | Inventory name of the default hypervisor, used when a VM doesn't specify its own `hypervisor_host`.  |
| `vm_facts_default_backup_host`       | :heavy_check_mark:       | Inventory name of the default backup server, used when a VM doesn't specify its own `backup_host`.   |
| `vm_facts_default_storage_host`      | :heavy_check_mark:       | Inventory name of the default storage server, used when a VM doesn't specify its own `storage_host`. |
| `vm_facts_limit_hosts`               | :heavy_multiplication_x: | If defined, only the hosts in this list will be considered for fact generation.                      |

`vm_facts_generate_storage_facts` and `vm_facts_generate_backup_facts` are mutually exclusive with `vm_facts_generate_storage_facts` being prioritized.

## Role Variables (needed for storage or backup)

| Name                                 |          Default / Mandatory          | Description                                                                                                                                                                                                                                                                                                                                                                                                          |
|:-------------------------------------|:-------------------------------------:|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `vm_facts_storage_zfs_parent_prefix` |               `'tank/'`               | [only needed on `storage` and `backup`] A prefix string for ZFS filesystems and ZVOLs, e.g. `tank/vms/`.                                                                                                                                                                                                                                                                                                             |
| `vm_facts_backup_zfs_parent_prefix`  |               `'tank/'`               | [only needed on `storage`] A prefix string for ZFS filesystems and ZVOLs, e.g. `tank/vms/`. This is used for setting the target filesystems on snapshot configurations (i.e. where on the backup host shall the filesystem on this storage host be placed). The full backup target filesystem is generated by appending the used `storage_host` of the vm and `/vms/`, followed by the organization and vm hostname. |
| `vm_facts_nfs_options`               |          `[no_root_squash]`           | [only needed on `storage`] A list of NFS options, e.g. a default IP that is added to all exports. The option format must conform to the ZFS `sharenfs` attribute format. The role adds by default the `hypervisor_host` or the default hypervisor_host IP as `rw=@{{ hypervisor_host.ansible_host }}` option.                                                                                                        |
| `vm_facts_default_root_reservation`  |                                       | [only needed on `storage` and `backup`] If this var is set (e.g. to `10G` or any other allowed value for ZFS `reservation` attribute), root filesystems will use it as reservation by default. Otherwise, the size of the VM will be set as reservation when choosing `storage`. Independently, custom `reservation` may be set in the `vm.filesystems` variable                                                     |
| `vm_facts_default_storage_type`      |             `filesystem`              | [only needed on `storage` and `backup`] This storage type will be chosen if the `vm` block does not specify one itself.                                                                                                                                                                                                                                                                                              |
| `iscsi_default_initiators`           | :heavy_check_mark: (if iSCSI is used) | [only needed on `storage`] This var is explained in [iscsi-target](https://github.com/stuvusIT/iscsi-target#role-variables).                                                                                                                                                                                                                                                                                         |
| `iscsi_default_portals`              | :heavy_check_mark: (if iSCSI is used) | [only needed on `storage`] This var is explained in [iscsi-target](https://github.com/stuvusIT/iscsi-target#role-variables).                                                                                                                                                                                                                                                                                         |

## Role Variables (hypervisor)
| Name                           | Default / Mandatory | Description                                                                                                                  |
|:-------------------------------|:-------------------:|:-----------------------------------------------------------------------------------------------------------------------------|
| `vm_facts_default_cidr_suffix` |        `/24`        | This suffix will be appended to all IPs in `vm.interfaces` if the IP in question does not already define a CIDR subnet mask. |

## Role Variables (VM hostvars)

As this role looks at all `hostvars`, some variables, especially the `vm` block are relevant. 
This table only lists the options used in this role, see [xen-vman](https://github.com/stuvusIT/xen_vman#vm-variables) for other possible and mandatory vars inside the `vm` dict.

### vm

| Name                   | Default / Mandatory                                                                                                                                                                                                                                 | Description                                                                                                                                                                                                                                                                                                                                                |
|:-----------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `org`                  | :heavy_check_mark:                                                                                                                                                                                                                                  | The organization this VM belongs to. Depending on this value, the filesystem or ZVOL will be placed in a different hierarchy.                                                                                                                                                                                                                              |
| `storage_type`         | `filesystem`                                                                                                                                                                                                                                        | Use `blockdevice` to create a ZVOL (ZFS virtual blockdevice of static size) and export it (as `{{ org }}-{{ name }}`) via iSCSI (only on `storage`). Use `filesystem` (the default) to create a root filesystem `{{ org }}/{{ name }}-root` and optionally other filesystems (see `filesystems`) and export them via NFS (only enabled on type `storage`). |
| `create_storage`       | `True`                                                                                                                                                                                                                                              | Whether to automatically create storage filesystems/blockdevices for this VM.                                                                                                                                                                                                                                                                              |
| `create_backup`        | `True`                                                                                                                                                                                                                                              | Whether to automatically create backup filesystems/blockdevices for this VM.                                                                                                                                                                                                                                                                               |
| `size`                 | :heavy_check_mark:                                                                                                                                                                                                                                  | Size of the root blockdevice or filesystem, e.g. `15G`. The size can only be changed later on if `storage_type`=`filesystem`.                                                                                                                                                                                                                              |
| `filesystems`          | `[{'name': root, 'zfs_attributes':{'quota': {{ size }}, 'reservation': {{ size &#124 default(vm_facts_default_root_reservation) }}}, 'nfs_options': {{ vm_facts_nfs_options }} + [rw=@{{ interface.ip }},rw=@{{ hypervisor_host.ansible_host }}]}]` | A list containing filesystem definitions, see [filesystems](#filesystems) - this var is only relevant if `storage_type=filesystem`.                                                                                                                                                                                                                        |
| `local_snapshots`      | `[hourly]`                                                                                                                                                                                                                                          | List of snapshot frequencies to be activated for [zfs-auto-snapshot](https://github.com/stuvusit/zfs-auto-snapshot). For blockdevices the attribute needs to be set here, for filesystems, the value may be overridden in `vm.filesystems`.                                                                                                                |
| `description`          | :heavy_check_mark:                                                                                                                                                                                                                                  | Description of this VM's purpose. This var may also be on the root level of the VM host in question.                                                                                                                                                                                                                                                       |
| `storage_host`         | `{{ vm_facts_default_storage_host }}`                                                                                                                                                                                                               | Storage host to use for this VM.                                                                                                                                                                                                                                                                                                                           |
| `hypervisor_host`      | `{{ vm_facts_default_hypervisor_host }}`                                                                                                                                                                                                            | Hypervisor host to use for this VM.                                                                                                                                                                                                                                                                                                                        |
| `backup_host`          | `{{ vm_facts_default_backup_host }}`                                                                                                                                                                                                                | Host to which this VM shall be backed up to.                                                                                                                                                                                                                                                                                                               |
| `pull_storage_from`    | :heavy_multiplication_x:                                                                                                                                                                                                                            | This will add a list item to the generated `vm_facts_move_storages` var, consisting of a dict containing the keys `source_storage`, `source_dataset`, `target_storage`, `target_dataset_suffix`, `source_backup_dataset`, `target_backup_dataset` and `backup_host`  needed to move a VM.                                                                  |
| `pull_hypervisor_from` | :heavy_multiplication_x:                                                                                                                                                                                                                            | This will add a list item to the generated `vm_facts_move_hypervisors` var, consisting of a dict containing the keys `source_hypervisor`, `destination_hypervisor`, `org` and `host` needed to move a VM.                                                                                                                                                  |

#### filesystems

`vm.filesystems` is a list of dicts that describe filesystems for one VM.
A `root` filesystem will always be created, with `quota` set to the VM `size` value, `reservation` set to the global default value or also the VM `size` (see above) and the the default NFS options as well as `no_root_squash` added.
On hosts with `vm_facts_variant`=`backup`, no NFS options will be added and the filesystems or volumes will be set to readonly and the `quota` set to `none`.
Quotas in ZFS sum up not only the filesystem, but also its decendants such as snapshots.
Therefore the quota intended for the storage of a VM will limit the amount of snapshots of it that can be stored on the backup host.
The `filesystems` var is only respected if `storage_type` is `filesystem`.

| Name              |                               Default / Mandatory                                | Description                                                                                                                                                                                                                                                                                                                              |
|:------------------|:--------------------------------------------------------------------------------:|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`            |                                :heavy_check_mark:                                | `name`-suffix of the filesystem. The final name consists of the vm name and the filesystem name, delimited by a dash.                                                                                                                                                                                                                    |
| `zfs_attributes`  |                                       `{}`                                       | A dict containing any ZFS attributes that shall be set for this filesystem. It is recommended to define a `quota`, though this may also be done in the default ZFS attributes on the actual [zfs-storage](https://github.com/stuvusIT/zfs-storage/) server.                                                                              |
| `nfs_options`     | `[no_root_squash,rw=@{{ ansible_host }},rw=@{{ hypervisor_host.ansible_host }}]` | A list of NFS options that are set for this NFS export. The options have to conform to the ZFS `sharenfs` attribute format. The options defined in `vm_nfs_options` will be set in addition to this value in every case. Also, read-write access will be granted to the VM and its hypervisor in every case (but not on backup servers). |
| `local_snapshots` |                            `{{ vm.local_snapshots }}`                            | List of snapshot frequencies to be activated for [zfs-auto-snapshot](https://github.com/stuvusit/zfs-auto-snapshot)                                                                                                                                                                                                                      |

## Example Playbook

### storage01 hostvars

```yml
vm_facts_generate_storage_facts: True
vm_facts_storage_zfs_parent_prefix: tank/vms/
iscsi_default_initiators:
 - name: 'iqn.1994-05.com.redhat:client1'
   authentication:
     userid: myuser
     password: mypassword
     userid_mutual: sharedkey
     password_mutual: sharedsecret
iscsi_default_portals:
 - ip: 192.168.10.3
vm_facts_nfs_options:
 - sync
vm_facts_default_root_reservation: 10G
interfaces:
 - ip: '192.168.10.3'
```

### hypervisor01 hostvars

```yml
vm_facts_generate_hypervisor_facts: True
interfaces:
 - ip: '192.168.10.2'
```

### web01 hostvars

```yml
vm:
  description: VM to host static websites
  memory: 2048
  vcpus: 4
  org: misc
  size: 15G
  storage_type: filesystem
  storage_host: storage01
  hypervisor_host: hypervisor01
  filesystems:
   - name: data
     zfs_attributes:
       quota: 50G
  interfaces:
   - mac: 'AA:BB:CC:FE:19:AA'
     ip:  '192.168.10.52'
   - mac: 'AA:BB:CC:FE:19:AB'
     ip:  '192.168.100.52'
ansible_host: 192.168.10.52
```

### Result

Assuming the vm is named `web01`, these two filesystems will be created on the storage server:

|            Name            | ZFS attributes                                                                               |
|:--------------------------:|:---------------------------------------------------------------------------------------------|
| `tank/vms/misc/web01-root` | `quota=15G`, `reservation=10G`, `sharenfs=no_root_squash,rw=@192.168.10.2,rw=@192.168.10.52` |
| `tank/vms/misc/web01-data` | `quota=50G`, `sharenfs=no_root_squash,rw=@192.168.10.2,rw=@192.168.10.52`                    |

The hypervisor will have an additional entry in his `xen_vman_vms` list:

```yml
xen_vman_vms:
 - description: VM to host static websites
   memory: 2048
   vcpus: 4
   org: misc
   size: 15G
   storage_host: storage01
   hypervisor_host: hypervisor01
   storage_type: filesystem
   interfaces:
    - mac: 'AA:BB:CC:FE:19:AA'
      ip:  '192.168.10.52'
    - mac: 'AA:BB:CC:FE:19:AB'
      ip:  '192.168.100.52'
```

Note that `filesystems` has been removed as it is not needed by the hypervisor.

## License

This work is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-sa/4.0/).

## Author Information

- [Michel Weitbrecht (SlothOfAnarchy)](https://github.com/SlothOfAnarchy) _michel.weitbrecht@stuvus.uni-stuttgart.de_
