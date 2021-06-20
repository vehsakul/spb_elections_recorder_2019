#!/bin/bash
set -e
user=root
target_dir=/root/elections

host=167.172.36.253
for i in {0..3}
do
  ssh ${user}@${host} "cd ${target_dir} && rm -f work-$i/{log.txt,error-log.txt}"
done

host=134.209.94.160
do
  ssh ${user}@${host} "cd ${target_dir} && rm -f work-$i/{log.txt,error-log.txt}"
done