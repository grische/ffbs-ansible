# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
    config.vm.box = "debian/stretch64"
    config.vm.network "public_network"

    config.vm.provision "ansible" do |ansible|
        ansible.playbook = "playbook.yml"
        ansible.inventory_path = "vagrant_inventory.ini"
    end

    config.vm.define "web", autostart: false do |web|
        web.vm.hostname = "web"
    end

    config.vm.define "concentrator" do |concentrator|
        concentrator.vm.hostname = "concentrator"
    end

    config.vm.define "client" do |client|
        client.vm.hostname = "client"
    end

    config.vm.provider "virtualbox" do |vb|
        vb.memory = "1024"
    end
end

