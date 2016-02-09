# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure(2) do |config|
  # For a complete reference of available confguration options, please see the
  # online documentation at https://docs.vagrantup.com.

  config.vm.box = "ubuntu/trusty32"

  config.vm.network "forwarded_port", guest: 8000, host: 8000
  # Enable this if you want host-only access to the machine using the given IP
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end

  config.vm.provision :shell, :path => "tools/install/install.sh"
end
