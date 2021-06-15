XAUTH=$HOME/.Xauthority
touch $XAUTH
DIR="$(dirname $0)"
SRC_DIR="$DIR/.."
xhost +local:docker
exec docker run --rm --interactive --network=host --ipc=host --env DISPLAY=$DISPLAY --volume $XAUTH:/root/.Xauthority --volume $HOME/.openerprc:/root/.openerprc --volume $SRC_DIR:/erpclient gisce/erpclient

