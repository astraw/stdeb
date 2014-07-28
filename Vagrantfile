# encoding: utf-8

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  # install prerequisites for stdeb and tests
  config.vm.provision :shell, :inline => "apt-get update"
  config.vm.provision :shell, :inline => "apt-get install --yes debhelper python-all-dev python-setuptools apt-file libxml2-dev libxslt1-dev python-requests python3-all-dev python3-setuptools"

  config.vm.provision :shell, :inline => "wget http://debs.strawlab.org/precise/python3-requests_2.3.0-0ads1_all.deb -O python3-requests_2.3.0-0ads1_all.deb"
  config.vm.provision :shell, :inline => "dpkg -i python3-requests_2.3.0-0ads1_all.deb"

  # We need to copy files to a new dir to prevent vagrant filesystem issues.
  config.vm.provision :shell, :inline => "cp -a /vagrant /tmp/vagrant_copy"

  # Install stdeb
  config.vm.provision :shell, :inline => "rm -rf /tmp/vagrant_copy/deb_dist"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && python setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True --with-python3=True --no-python3-scripts=True install_deb"

  # Run tests.
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test.sh"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test-pypi-install.sh"

  # Run tests on Python 3.
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && mkdir bin && ln -s /usr/bin/python3 bin/python"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && PATH=/tmp/vagrant_copy/bin:${PATH} ./test.sh"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && PATH=/tmp/vagrant_copy/bin:${PATH} ./test-pypi-install.sh"

end
