#!/bin/bash
set -e
shopt -s extglob

user=root
target_dir=/root/elections

for host in 167.172.36.253 134.209.94.160
do
  ssh ${user}@${host} "mkdir -p ${target_dir}"
  scp dist/cli ${user}@${host}:${target_dir}
  for i in {0..3}
  do
    rm -f work-$i/log.txt*
    ssh ${user}@${host} "mkdir -p ${target_dir}/work-$i"
    scp logconf.prod.yml cameras.csv ${user}@${host}:${target_dir}/work-$i
  done
done


