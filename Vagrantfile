# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "debian/stretch64"
    #config.vm.network "public_network"

    config.vm.synced_folder ".", "/vagrant", type: "rsync",
        rsync__exclude: ".git/"

    config.vm.provision "ansible" do |ansible|
        ansible.verbose = "v"
        ansible.playbook = "playbook.yml"
        ansible.groups = {
            "WebServers" => ["web"],
            "Concentrators" => ["concentrator1", "concentrator2", "concentrator3"],
            "Clients" => ["client"],
        }
        ansible.host_vars = {
            "concentrator1" => {"etcd_peer_ip" => "192.168.122.11"},
            "concentrator2" => {"etcd_peer_ip" => "192.168.122.12"},
            "concentrator3" => {"etcd_peer_ip" => "192.168.122.13"},
        }
    end

    config.vm.define "web", autostart: false do |web|
        web.vm.hostname = "web"
    end

    config.vm.define "concentrator1" do |concentrator|
        concentrator.vm.hostname = "concentrator1"
        concentrator.vm.network :private_network,
            :ip => "192.168.122.11",
            :libvirt__network_name => "backbone"
    end

    config.vm.define "concentrator2" do |concentrator|
        concentrator.vm.hostname = "concentrator2"
        concentrator.vm.network :private_network,
            :ip => "192.168.122.12",
            :libvirt__network_name => "backbone"
    end

    config.vm.define "concentrator3" do |concentrator|
        concentrator.vm.hostname = "concentrator3"
        concentrator.vm.network :private_network,
            :ip => "192.168.122.13",
            :libvirt__network_name => "backbone"
    end

    config.vm.define "client" do |client|
        client.vm.hostname = "client"
    end

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "1024"
    end
end

