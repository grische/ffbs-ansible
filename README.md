# Ansible for Parker

This is a fork of the Freifunk Braunschweig ansible repository.
See <https://gitli.stratum0.org/ffbs/ffbs-ansible>

## How to run it

1. Create an inventory file `ffmuc-inventory` with the parker gateway at 192.168.0.2. For example:

   ```ini
   [Backbone]
   parker-vm01 ansible_host=192.168.0.2

   [etcd_cluster]
   parker-vm01 ansible_host=192.168.0.2

   [etcd_clients]
   parker-vm01 ansible_host=192.168.0.2

   [Concentrators]
   parker-vm01 ansible_host=192.168.0.2
   ```

1. Generate a new wireguard keypair and add them to [parker-vm01/vars](host_vars/parker-vm01/vars)

   ```sh
   privkey=$(wg genkey)
   pubkey=$(wg pubkey <<< ${privkey})
   echo "wg_private_key: '${privkey}'"
   echo "wg_public_key: '${pubkey}'"
   ```

1. Generate custom certificates:

   ```sh
    ./etcd-ca/openssl-ca.sh
   ```

1. Create a `.vault` file containing the password that was used for the custom certificates:

   ```sh
   echo "mypassword" > .vault
   ```

1. Generate a new node-config keypair

   ```sh
   ./node-config-keygen.sh
   ```

1. Run the playbook:

   ```sh
   ansible-playbook -v -i ffmuc-inventory playbook-ffmuc.yml
   ```
