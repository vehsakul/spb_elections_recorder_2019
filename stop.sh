#!/bin/bash
set -e
user=root
target_dir=/root/elections

host=167.172.36.253
for i in {0..3}
do
  ssh ${user}@${host} "cd ${target_dir} && pm2 delete cli-$i"
done

host=134.209.94.160
for i in {0..3}
do
  ssh ${user}@${host} "cd ${target_dir} && pm2 delete cli-$i"
done