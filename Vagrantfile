# -*- mode: ruby -*-
# vi: set ft=ruby :

ENV['VAGRANT_DEFAULT_PROVIDER'] = 'libvirt'
Vagrant.configure("2") do |config|
    #config.vm.box = "debian/stretch64"
    # use box with VRF support (kernel and iproute2)
    config.vm.box = "jluebbe/ffbs-base"
    config.vm.box_version = "20190109.0.0"
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
            "Exits" => ["exit1"],
            "Nodes" => ["node1", "node2", "node3"],
            "UCI-Nodes" => ["node2", "node3"],
            "Backbone" => ["concentrator1", "concentrator2", "concentrator3", "exit1"],
        }
        #ansible.tags = "devel"
    end

    config.vm.define "web", autostart: false do |web|
        web.vm.hostname = "web"
    end

    config.vm.define "concentrator1" do |concentrator|
        concentrator.vm.hostname = "concentrator1"
    end

    config.vm.define "concentrator2" do |concentrator|
        concentrator.vm.hostname = "concentrator2"
    end

    config.vm.define "concentrator3" do |concentrator|
        concentrator.vm.hostname = "concentrator3"
    end

    config.vm.define "client" do |client|
        client.vm.hostname = "client"
        client.vm.network :private_network,
            :libvirt__network_name => "access1",
            :libvirt__iface_name => "client-access",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
    end

    config.vm.define "exit1" do |exit|
        exit.vm.hostname = "exit1"
    end

    config.vm.define "node1" do |node|
        node.vm.hostname = "node1"
        node.vm.network :private_network,
            :libvirt__network_name => "mesh",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
        node.vm.network :private_network,
            :libvirt__network_name => "access1",
            :libvirt__iface_name => "node1-access",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
    end

    config.vm.define "node2" do |node|
        node.vm.box = "jluebbe/ffbs-openwrt-snapshot"
        node.vm.box_version = "20190109.0.0"
        node.vm.network :private_network,
            :libvirt__network_name => "mesh",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
        node.vm.network :private_network,
            :libvirt__network_name => "access2",
            :libvirt__iface_name => "node2-access",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
    end

    config.vm.define "node3" do |node|
        node.vm.box = "jluebbe/ffbs-openwrt-snapshot"
        node.vm.box_version = "20190109.0.0"
        node.vm.network :private_network,
            :libvirt__network_name => "mesh",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
        node.vm.network :private_network,
            :libvirt__network_name => "access3",
            :libvirt__iface_name => "node3-access",
            :libvirt__forward_mode => "veryisolated",
            :libvirt__dhcp_enabled => false,
            :autostart => true
    end

    config.vm.provider "libvirt" do |libvirt|
        libvirt.cpus = 2
        libvirt.memory = 512
        libvirt.random :model => 'random'
        libvirt.disk_bus = 'sata' # support fstrim
    end
end


