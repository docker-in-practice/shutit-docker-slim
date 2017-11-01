import random
import string
import os
import inspect

# See T148

from shutit_module import ShutItModule

class shutit_docker_slim(ShutItModule):


	def build(self, shutit):
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		run_dir = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		module_name = 'shutit_docker_slim_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.send('command rm -rf ' + run_dir + '/' + module_name + ' && command mkdir -p ' + run_dir + '/' + module_name + ' && command cd ' + run_dir + '/' + module_name)
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(run_dir + '/' + module_name + '/Vagrantfile','''
Vagrant.configure(2) do |config|
  config.vm.box = "''' + vagrant_image + '''"
  # config.vm.box_check_update = false
  # config.vm.network "forwarded_port", guest: 80, host: 8080
  # config.vm.network "private_network", ip: "192.168.33.10"
  # config.vm.network "public_network"
  # config.vm.synced_folder "../data", "/vagrant_data"
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
    vb.name = "shutit_docker_slim"
  end
end''')
        # Try and pick up sudo password from 'secret' file (which is gitignored).
		try:
			pw = open('secret').read().strip()
		except:
			pw = shutit.get_env_pass()
		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'],{'assword for':pw},timeout=99999)
		except:
			shutit.multisend('vagrant up',{'assword for':pw},timeout=99999)
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su -',password='vagrant')
		shutit.install('docker')
		shutit.install('git')
		shutit.install('unzip')

		# Install docker-slim
		shutit.send('wget https://github.com/docker-slim/docker-slim/releases/download/1.17/dist_linux.zip',note='Get docker slim')
		shutit.send('unzip dist_linux.zip')
		shutit.send('mv dist_linux docker-slim-bin')

		# create simple app, run and run docker-slim on it.
		shutit.send('git clone https://github.com/docker-slim/docker-slim.git')
		shutit.send('cd docker-slim/examples/apps/node_ubuntu',note='Build the sample node app')
		shutit.send('docker build -t sample-node-app .')

		# Run docker-slim
		shutit.send('cd /root/docker-slim-bin')
		shutit.send('./docker-slim build --http-probe sample-node-app &',note='''Run docker-slim with an http probe. An http probe is TODO''')
		shutit.send('sleep 10 && curl localhost:32770',note='Wait a little for the program to start up, and use the application to exercise its code. In a real context, and with a larger and more complex app this might be more thorough.')
		shutit.send('fg',expect='probe done',note='Foreground the task to let it finish.')
		shutit.send('',note='Hit return when done.')

		# image created
		shutit.send('docker images',note='sample-node-app.slim has been created by the docker slim process')
		shutit.send('docker history sample-node-app.slim',note='sample-node-app.slim history - much smaller')
		# seccomp
		shutit.send('cat /root/docker-slim-bin/.images/*/artifacts/sample-node-app-seccomp.json',note='Examine the generated seccomp profile')
		d = shutit.send_and_get_output('ls /root/docker-slim-bin/.images',note='Examine the generated seccomp profile')
		# Compare list to here of blocked ones: https://docs.docker.com/engine/security/seccomp/
		shutit.send('docker run -d --security-opt seccomp=/root/docker-slim-bin/.images/' + d + '/artifacts/sample-node-app-seccomp.json sample-node-app',note='Run against the original fat image or slim one if you prefer')
		shutit.send('docker run -p32770:8000 -d --security-opt seccomp=/root/docker-slim-bin/.images/' + d + '/artifacts/sample-node-app-seccomp.json sample-node-app.slim',note='Run the slim app to show it works')
		shutit.send('sleep 10 && curl localhost:32770',note='Wait a little for the program to start up, and use the application to exercise its code. In a real context, and with a larger and more complex app this might be more thorough.')

		shutit.pause_point('look at bash history - there is also the seccomp command run above')

		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='ubuntu/xenial64')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='512')
		return True


def module():
	return shutit_docker_slim(
		'shutit.shutit_docker_slim.shutit_docker_slim', 2129399610.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualbox.virtualbox.virtualbox','tk.shutit.vagrant.vagrant.vagrant']
	)
