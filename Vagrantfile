# encoding: utf-8

# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box_url = "http://dl.dropbox.com/u/54390273/vagrantboxes/Squeeze64_VirtualBox4.2.4.box"
  config.vm.box = "debian-squeeze-64-vanilla"

  # install prerequisites for stdeb and tests
  config.vm.provision :shell, :inline => "apt-get update"
  config.vm.provision :shell, :inline => <<-SH
    export DEBIAN_FRONTEND=noninteractive
    apt-get install --yes debhelper python-all-dev python-setuptools apt-file python3-all-dev libpq-dev python-argparse python3-setuptools
    curl https://bootstrap.pypa.io/ez_setup.py | python
    easy_install pip==1.5.6
    pip2 install requests==2.4.3
    easy_install3 pip==1.5.6
    pip3 install argparse==1.3.0
    pip3 install backports.ssl_match_hostname
    pip3 install requests==2.4.3
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
