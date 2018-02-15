ethtool_exporter
================

A Prometheus exporter for statistics from NIC drivers exposed by
`ethtool -S <interface>`.


Ansible installation example
============================

I use Supervisor on Ubuntu 14.04 and Debian 7. For Ubuntu 16.04 and
Debian 8+, I'd create a systemd unit file instead.

  tasks:

    - name: install virtualenv and supervisor
      apt:
        name: "{{ item }}"
        state: present
      with_items:
        - python-virtualenv
        - supervisor

    - name: create the /opt/ethtool_exporter directory
      file:
        dest: /opt/ethtool_exporter
        state: directory

    - name: create a virtualenv and install prometheus_client
      pip:
        name: prometheus_client
        state: present
        virtualenv: /opt/ethtool_exporter/virtualenv

    - name: install ethtool_exporter
      copy:
        url: https://raw.githubusercontent.com/adeverteuil/ethtool_exporter/master/ethtool_exporter.py
        dest: /opt/ethtool_exporter/ethtool_exporter
        mode: 0744

    - name: create the ethtool_exporter user
      user:
        name: ethtool_exporter
        state: present
        system: yes

    - name: Supervise ethtool_exporter
      copy:
        dest: /etc/supervisor/conf.d/ethtool_exporter.conf
        content: |
          [program:ethtool_exporter]
          command = /opt/ethtool_exporter/ethtool_exporter
          environment = PATH="/opt/ethtool_exporter/virtualenv/bin:%(ENV_PATH)s",VIRTUAL_ENV="/opt/ethtool_exporter/virtualenv"
          user = ethtool_exporter
      notify: restart ethtool_exporter

    - name: add ethtool_exporter to Supervisor
      supervisorctl:
        name: ethtool_exporter
        state: present

    - name: start ethtool_exporter
      supervisorctl:
        name: ethtool_exporter
        state: started

  handlers:

    - name: restart ethtool_exporter
      supervisorctl:
        name: ethtool_exporter
        state: restarted


Developing
==========

    pyenv virtualenv ethtool_exporter  # Create a virtualenv.
    pyenv local ethtool_exporter       # Set the Python version for the CWD to it.
    pyenv activate ethtool_exporter    # Now activate the virtualenv.
    pip install -r requirements.txt    # Install dependencies.
    python tests.py                    # Run unit tests.

Assuming you use Pyenv with the pyenv-virtualenv plugin to manage Python
virtualenvs.

    https://github.com/pyenv/pyenv-installer


Useful references
=================

https://prometheus.io/docs/instrumenting/writing_exporters/
https://github.com/prometheus/client_python#custom-collectors
