#!/usr/bin/env bash
#
# SSH KEY GENERATION
#
# Description:
#	We are creating RSA encryption public and private keys for the base
#	Then, the private key is added to the 'ssh-agent' service, which will
#	handle passwordless access in the future.
#	Lastly, we ssh into the remote machine to copy over the authorized key
#	from the base and set it with the approapriate access permissions. 
#
# Notes:
#	The following steps must occur sequentially.
#	Each command depends on the success of the last.
#
#	We use the program sshpass to pass in the remote password without having
#	a human type it in.
#
#	We use StrictHostKeyChecking=no to prevent the user having
#	to verify manually that we would like to connect to the remote.
#
#	We useIdentitiesOnly=yes to tell the host to only use the available
#	authentication identity file configured in ssh_config files, even if
#	ssh-agent offers more identities.

# Parse args
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --password)
    ROBOT_PASSWORD=$2
    shift
    shift
    ;;
    --username)
    ROBOT_USERNAME=$2
    shift
    shift
    ;;
    --hostname)
    ROBOT_HOSTNAME=$2
    shift
    shift
    ;;
esac
done

# Check for network connectivity
#ping $ROBOT_HOSTNAME -c 4
# TODO grab output and use to provide feedback

# First export robot username and hostname to bashrc
echo "export ROBOT_HOSTNAME=${ROBOT_HOSTNAME}" >> ~/.bashrc
echo "export ROBOT_USERNAME=${ROBOT_USERNAME}" >> ~/.bashrc
echo "export ROBOT_HOSTNAME=${ROBOT_HOSTNAME}" >> ~/.xsessionrc
echo "export ROBOT_USERNAME=${ROBOT_USERNAME}" >> ~/.xsessionrc

# If both files are present don't generate keys, use existing.
if [[ -f ~/.ssh/id_rsa && -f ~/.ssh/id_rsa.pub ]]; 
then
        ssh-add \
        && cat ~/.ssh/id_rsa.pub | \
        sshpass -p "$ROBOT_PASSWORD" \
        ssh -vvv -o StrictHostKeyChecking=no \
        -o IdentitiesOnly=yes \
        $ROBOT_USERNAME@$ROBOT_HOSTNAME \
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys"

# If neither file is present, generate keys.
elif [[ ! -f ~/.ssh/id_rsa && ! -f ~/.ssh/id_rsa.pub ]];
then
        ssh-keygen -f ~/.ssh/id_rsa -t rsa -N "" \
        && ssh-add \
        && cat ~/.ssh/id_rsa.pub | \
        sshpass -p "$ROBOT_PASSWORD" \
        ssh -vvv -o StrictHostKeyChecking=no \
        -o IdentitiesOnly=yes \
        $ROBOT_USERNAME@$ROBOT_HOSTNAME \
        "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys"

# If only one file is present, give error to manually fix it.
else
    echo "You have only a private or only a public ssh key. You must either
        delete one of them, or regenerate new keys, and re-run this."
    exit 1
fi 

# If one file is missing 

# You can delete these keys via ssh-add -D
    
# Search through remote's .bashrc file for catkin workspace filepath.
# Note:
#	Vanilla ssh login only allows us to see a subset of the remote's
#	environment variables. Specifically, we can only see variables listed
#	under the remote's /.ssh/environment file. To bypass this problem,
#	we search through the remote's /.bashrc file for the 'export' command
#	associated with the environment variable of interest. We copy the
#	complete export command into our very own /bashrc file.
ROBOT_CATKIN=$(ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes $ROBOT_USERNAME@$ROBOT_HOSTNAME 'cat ~/.bashrc | grep ROBOT_CATKIN')
ROBOT_PROJECT_CRUNCH_PATH=$(ssh -o StrictHostKeyChecking=no -o IdentitiesOnly=yes $ROBOT_USERNAME@$ROBOT_HOSTNAME 'cat ~/.bashrc | grep ROBOT_PROJECT_CRUNCH_PATH')

echo "$ROBOT_CATKIN_PATH" >> ~/.bashrc
echo "$ROBOT_PROJECT_CRUNCH_PATH" >> ~/.bashrc
echo "$ROBOT_CATKIN_PATH" >> ~/.xsessionrc
echo "$ROBOT_PROJECT_CRUNCH_PATH" >> ~/.xsessionrc
