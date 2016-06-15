# Installing the F5 app from source code

On the phantom userid, create a directory named 

/home/phantom/app_dev/f5_firewall

touch __init__.py


## Download the F5 REST module

curl -o icontrol_install_config.py https://raw.githubusercontent.com/joelwking/ansible-f5/master/icontrol_install_config.py

## Create a flake configuration file (optional)

In directory /home/phantom/.config  create a file named flake8 


[flake8]
ignore = E402,F403,E128,E126,E111,E121,E127
max-line-length = 180
max-complexity = 28



