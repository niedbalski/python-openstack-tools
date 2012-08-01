#
# This document serves as an example of how to deploy
# basic single and multi-node openstack environments.
#

# deploy a script that can be used to test nova
class { 'openstack::test_file': }

####### shared variables ##################


# this section is used to specify global variables that will
# be used in the deployment of multi and single node openstack
# environments

$public_interface        = "$d_public_interface"
$private_interface       = "$d_private_interface" 
$admin_email             = "$d_admin_email"
$admin_password          = "$d_admin_password"
$keystone_db_password    = "$d_keystone_db_password"
$keystone_admin_token    = "$d_keystone_admin_token"
$nova_db_password        = "$d_nova_db_password"
$nova_user_password      = "$d_nova_user_password"
$glance_db_password      = "$d_glance_db_password"
$glance_user_password    = "$d_glance_user_password"
$rabbit_password         = "$d_rabbit_password"
$rabbit_user             = "$d_rabbit_user"
$fixed_network_range     = "$d_fixed_network_range"
$floating_network_range  = "$d_floating_network_range"
$verbose                 = $d_verbose
$auto_assign_floating_ip = $d_auto_assign_floating_ip
$libvirt_type            = "$d_libvirt_type"

#### end shared variables #################

# all nodes whose certname matches openstack_all should be
# deployed as all-in-one openstack installations.
node /openstack_all/ {

  class { 'openstack::all':
    #public_address          => $ipaddress_eth0,
    public_interface        => $public_interface,
    private_interface       => $private_interface,
    admin_email             => $admin_email,
    admin_password          => $admin_password,
    keystone_db_password    => $keystone_db_password,
    keystone_admin_token    => $keystone_admin_token,
    nova_db_password        => $nova_db_password,
    nova_user_password      => $nova_user_password,
    glance_db_password      => $glance_db_password,
    glance_user_password    => $glance_user_password,
    rabbit_password         => $rabbit_password,
    rabbit_user             => $rabbit_user,
    libvirt_type            => $libvirt_type,
    floating_range          => $floating_network_range,
    fixed_range             => $fixed_network_range,
    verbose                 => $verbose,
    auto_assign_floating_ip => $auto_assign_floating_ip,
  }

  class { 'openstack::auth_file':
    admin_password       => $admin_password,
    keystone_admin_token => $keystone_admin_token,
    controller_node      => '127.0.0.1',
  }

}

# multi-node specific parameters

$controller_node_address  = "$d_controller_node_address"
$controller_node_public   = $controller_node_address
$controller_node_internal = $controller_node_address

$sql_connection         = "mysql://nova:${nova_db_password}@${controller_node_internal}/nova"

node /openstack_controller/ {

 class { 'openstack::controller':
    public_address          => $controller_node_public,
    public_interface        => $public_interface,
    private_interface       => $private_interface,
    internal_address        => $controller_node_internal,
    floating_range          => $floating_network_range,
    fixed_range             => $fixed_network_range,
    multi_host              => true,
    network_manager         => 'nova.network.manager.FlatDHCPManager',
    verbose                 => $verbose,
    auto_assign_floating_ip => $auto_assign_floating_ip,
    mysql_root_password     => $mysql_root_password,
    admin_email             => $admin_email,
    admin_password          => $admin_password,
    keystone_db_password    => $keystone_db_password,
    keystone_admin_token    => $keystone_admin_token,
    glance_db_password      => $glance_db_password,
    glance_user_password    => $glance_user_password,
    nova_db_password        => $nova_db_password,
    nova_user_password      => $nova_user_password,
    rabbit_password         => $rabbit_password,
    rabbit_user             => $rabbit_user,
    export_resources        => false,
  }

  class { 'openstack::auth_file':
    admin_password       => $admin_password,
    keystone_admin_token => $keystone_admin_token,
    controller_node      => $controller_node_internal,
  }

}

node /openstack_compute/ {
  class { 'openstack::compute':
    public_interface   => $public_interface,
    private_interface  => $private_interface,
    internal_address   => $ipaddress_$d_public_interface,
    libvirt_type       => $libvirt_type,
    fixed_range        => $fixed_network_range,
    network_manager    => 'nova.network.manager.FlatDHCPManager',
    multi_host         => true,
    sql_connection     => $sql_connection,
    nova_user_password => $nova_user_password,
    rabbit_host        => $controller_node_internal,
    rabbit_password    => $rabbit_password,
    rabbit_user        => $rabbit_user,
    glance_api_servers => "${controller_node_internal}:9292",
    vncproxy_host      => $controller_node_public,
    vnc_enabled        => true,
    verbose            => $verbose,
    manage_volumes     => true,
    nova_volume        => 'nova-volumes'
  }

}
