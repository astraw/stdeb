# encoding: utf-8

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box_url = "https://dl.dropboxusercontent.com/s/3jz559mjz2aw4gs/debian-wheezy-64-vanilla.box"
  config.vm.box = "debian-wheezy-64-vanilla"

  # install prerequisites for stdeb and tests
  config.vm.provision :shell, :inline => "apt-get update"
  config.vm.provision :shell, :inline => <<-SH
    export DEBIAN_FRONTEND=noninteractive
    apt-get install --yes debhelper python-all-dev python-setuptools apt-file python-requests python3-all-dev python3-setuptools libpq-dev
    wget http://debs.strawlab.org/precise/python3-requests_2.3.0-0ads1_all.deb -O python3-requests_2.3.0-0ads1_all.deb
    dpkg -i python3-requests_2.3.0-0ads1_all.deb
SH

  # We need to copy files to a new dir to prevent vagrant filesystem issues.
  config.vm.provision :shell, :inline => "cp -a /vagrant /tmp/vagrant_copy"

  # Install stdeb
  config.vm.provision :shell, :inline => "rm -rf /tmp/vagrant_copy/deb_dist"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && python setup.py --command-packages=stdeb.command sdist_dsc --with-python2=True --with-python3=True --no-python3-scripts=True install_deb"

  # Run tests.
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test.sh"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test-pypi-install.sh"

  # Run tests on Python 3.
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && PYEXE=/usr/bin/python3 ./test.sh"
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && PYEXE=/usr/bin/python3 ./test-pypi-install.sh"

  # Run more tests
  config.vm.provision :shell, :inline => "cd /tmp/vagrant_copy && ./test2and3.sh"

end
