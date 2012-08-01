STACK_CONFIG = "./stack.yml"
STACK_CONFIG_CONTROLLER_ONLY = "./controller.yml"
STACK_CONFIG_COMPUTE_ONLY = "./compute.yml"

#vms
VM_RAM="2048"
VM_HOME=/home/aktive/vms
VM_ISO=/home/aktive/Downloads/ubuntu-12.04-server-amd64.iso

#preseed
PRESEED_URL="http://192.168.122.1/~aktive/kickstarts/ubuntu-server.preseed"


env:
	@if ! test -f ./env; then \
		virtualenv env; \
		./env/bin/activate; \
		pip install -r requeriments.txt; \
	fi;

all:
	python stack.py --config=${STACK_CONFIG} --upgrade=True

controller:
	python stack.py --config=${STACK_CONFIG_CONTROLLER_ONLY} --nova-volumes=True --puppet-master=True

compute:
	python stack.py --config=${STACK_CONFIG_COMPUTE_ONLY} --reboot=True --nova-volumes=True

