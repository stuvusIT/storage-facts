#!/usr/bin/env python3
# This script generates hypervisor (xen) facts out of the hostvars of each VM
import json
import optparse
import re


def main():
  p = optparse.OptionParser(
    description='Sets the relevant ansible facts needed for a xen hypervisor.',
    usage='%prog [hypervisor hostname] [path to file containing hostvars in json]')
  options, arguments = p.parse_args()
  if len(arguments) == 2:
    hypervisor_host = arguments[0]
    original_facts = json.loads(open(arguments[1]).read())
    facts = generateFacts(original_facts, hypervisor_host)
    print(json.dumps(facts))
  else:
    p.print_help()


def generateFacts(original_facts, hypervisor_host):
  # facts are the hostvars of the current hypervisor host
  facts = original_facts[hypervisor_host] if hypervisor_host in original_facts else {}
  cidr_suffix = facts['vm_facts_default_cidr_suffix'] if 'vm_facts_default_cidr_suffix' in facts else '/24'
  # List of hostnames that have missing VM vars. This lists will be printed in tasks for easier debugging
  failed_names = {'interfaces': [], 'description': []}
  default_hypervisor = facts['vm_facts_default_hypervisor_host']

  # Create list if it doesn't already exist
  if 'xen_vman_vms' not in facts:
    facts['xen_vman_vms'] = []
  if 'vm_facts_move_hypervisors' not in facts:
    facts['vm_facts_move_hypervisors'] = []

  # Traverse every host defined in hostvars
  for host in original_facts.keys():
    # Ignore physical hosts
    if 'vm' not in original_facts[host]:
      continue
    # config is the vm dict of a specific VM host
    config = original_facts[host]['vm']
    # Limit hosts to those defined in vm_facts_limit_hosts
    if 'vm_facts_limit_hosts' in facts and host not in facts['vm_facts_limit_hosts']:
      continue
    hypervisor_for_vm = config['hypervisor_host'] if 'hypervisor_host' in config else default_hypervisor
    if hypervisor_host != hypervisor_for_vm and (
        'pull_hypervisor_from' not in config or config['pull_hypervisor_from'] != hypervisor_host):
      continue
    # Limit hosts to those defined in vm_facts_limit_hosts
    if 'vm_facts_limit_hosts' in facts and host not in facts['vm_facts_limit_hosts']:
      continue

    config = original_facts[host]['vm']
    config['name'] = host
    # Ignore manually defined vms
    if any((d['name'] == host and 'org' in config and d['org'] == config['org']) for d in facts['xen_vman_vms']):
      continue
    if 'storage_type' in config:
      storage_type = config['storage_type']
    elif 'vm_facts_default_storage_type' in facts:
      storage_type = facts['vm_facts_default_storage_type']
    else:
      storage_type = 'filesystem'
    # Set precise connection type for xen, depending on general storage_type
    if storage_type == 'blockdevice':
      config['storage_type'] = 'iscsi'
    else:
      config['storage_type'] = 'nfs'

    # Copy description if necessary
    if 'description' not in config:
      if 'description' in original_facts[host]:
        config['description'] = original_facts[host]['description']
      else:
        failed_names['description'].append(host)

    # Copy interfaces if necessary
    if 'interfaces' not in config:
      if 'interfaces' in original_facts[host]:
        config['interfaces'] = original_facts[host]['interfaces']
      else:
        failed_names['interfaces'].append(host)

    # Set CIDR subnet mask
    for interface in config['interfaces']:
      if 'ip' in interface and not re.search("/[0-9]+", interface['ip']):
        interface['ip'] = interface['ip'] + cidr_suffix

    # Remove unneeded filesystems attribute
    if 'filesystems' in config:
      del config['filesystems']

    if hypervisor_host == hypervisor_for_vm:
      facts['xen_vman_vms'].append(config)
    elif 'pull_hypervisor_from' in config and config['pull_hypervisor_from'] == hypervisor_host:
      # Collect data needed to move VM datasets
      facts['vm_facts_move_hypervisors'].append(
        {'org': config['org'], 'host': host, 'source_hypervisor': hypervisor_host,
         'destination_hypervisor': hypervisor_for_vm})

  # Return the result, consisting of the failed hosts and the extended hostvars for the current hypervisor
  result = {'failed_hosts': failed_names, 'new_hostvars': facts}
  return result


if __name__ == "__main__":
  main()
