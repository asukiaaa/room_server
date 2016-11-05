# room_server
Using Raspberry pi and TOCOS TWE-Lite

# Setup

## Clone this repo to your pi

```sh
git clone git@github.com:asukiaaa/room_server.git /home/pi/room_server
git submodule init
git submodule update
```

## Install components

```sh
sudo apt-get install python-yaml
```

## Test local python programs

```sh
python /home/pi/room_server/local/socket_server.py &
python /home/pi/room_server/local/tocostick.py -p
```

## Apache setting

```sh
sudo apt-get install apache2 libapache2-mod-python
```

add following lines to `/etc/apache2/sites-available/default`

```
   <Directory /var/www/>
     Options Indexes FollowSymLinks MultiViews
     AllowOverride None
     Order allow,deny
     allow from all
     AddHandler mod_python .py          # added
     PythonHandler mod_python.publisher # added
     PythonDebug On                     # added
   </Directory>
```

then

```
sudo service apache2 reload
```

## Create symlink to /var/www

```sh
cd /var/www
ln -s /home/pi/room_server/network ./room
```

# Run

```
/home/pi/room_server/local/start_after_boot.sh
```

# Auto start setting

Add following line to `/etc/rc.local` before exit 0

```
sh /home/pi/room_server/local/start_after_boot.sh
```

or command

```
sudo sed -i '/^exit 0/ish \/home\/pi\/room_server\/local\/start_after_boot.sh' /etc/rc.local
```
