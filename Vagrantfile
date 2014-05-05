# encoding: utf-8

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  # install prerequisites for stdeb and tests
  config.vm.provision :shell, :inline => "apt-get update"
  config.vm.provision :shell, :inline => "apt-get install --yes debhelper python-all-dev python-setuptools apt-file libxml2-dev libxslt1-dev"

  # We need to copy files to a new dir to prevent vagrant filesystem issues.
  config.vm.provision :shell, :inline => "cp -a /vagrant /tmp/vagrant_copy"

  # Install stdeb
  config.vm.provision :shell, :inline => "rm -rf /tmp/vagrant_copy/deb_dist"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && python setup.py --command-packages=stdeb.command bdist_deb"
  config.vm.provision :shell, :inline => "dpkg -i /tmp/vagrant_copy/deb_dist/*.deb"

  # Run tests.
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test.sh"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test-pypi-install.sh"
end
