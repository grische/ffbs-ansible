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
            "Exits" => ["exit1"],
            "Nodes" => ["node1"],
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
    end

    config.vm.define "exit1" do |concentrator|
        concentrator.vm.hostname = "exit1"
    end

    config.vm.define "node1" do |concentrator|
        concentrator.vm.hostname = "node1"
    end

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "1024"
    end
    config.vm.provider "libvirt" do |libvirt|
        libvirt.cpus = 2
    end
end

