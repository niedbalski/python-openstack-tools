augtool << EOF
set /files/etc/puppet/puppet.conf/master/storeconfigs true
set /files/etc/puppet/puppet.conf/master/dbadapter sqlite3
set /files/etc/puppet/puppet.conf/master/dblocation /var/lib/puppet/server_data/storeconfigs.sqlite
save
EOF
