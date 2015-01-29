# 2015.01 by asukiaaa

### copy this repo to your pi

git clone git@github.com:asukiaaa/room_server.git /home/pi/
git submodule init
git submodule update

## install components
sudo apt-get install python-yaml

## you can test local python programs by
# python /home/pi/room_server/local/socket_server.py &
# python /home/pi/room_server/local/tocostick.py -p


### set up apache

sudo apt-get install apache2 libapache2-mod-python

## add following lines
## to /etc/apache2/sites-available/default 
#   <Directory /var/www/>
#     Options Indexes FollowSymLinks MultiViews
#     AllowOverride None
#     Order allow,deny
#     allow from all
#     AddHandler mod_python .py          # added
#     PythonHandler mod_python.publisher # added
#     PythonDebug On                     # added
#   </Directory>

## then
sudo service apache2 reload

### create symlink to /var/www

cd /var/www
ln -s /home/pi/room_server/network ./room


### add shell to auto start
## add following line
## to /etc/rc.local
# sh /home/pi/room_server/local/start_after_boot.sh # added before exit 0
# exit 0

## or command
sudo sed -i '/^exit 0/ish \/home\/pi\/room_server\/local\/start_after_boot.sh' /etc/rc.local
