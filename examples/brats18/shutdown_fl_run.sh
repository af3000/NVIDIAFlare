workspace=$1
site_pre="site-"
n_clients=$2

if test -z "$1" || test -z "${workspace}"
then
      echo "Usage: ./shutdown_fl_run.sh [workspace], e.g. ./shutdown_fl_run.sh poc_workspace 2"
      exit 1
fi

if [ "${workspace}" = "secure_workspace" ]
then
  SERVERNAME="localhost"
else
  SERVERNAME="server"
fi

echo "Attempting to shutdown ${n_clients} clients"
for id in $(eval echo "{1..$n_clients}")
do
  export CUDA_VISIBLE_DEVICES=1
  ./workspaces/${workspace}/${site_pre}${id}/startup/stop_fl.sh &
done

echo "Attempting to shutdown server at ${workspace}/${SERVERNAME}"
export CUDA_VISIBLE_DEVICES=1
./workspaces/${workspace}/${SERVERNAME}/startup/stop_fl.sh &

