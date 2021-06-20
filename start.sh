#!/bin/bash
set -e
user=root
target_dir=/root/elections

host=167.172.36.253
for i in {0..3}
do
  ssh ${user}@${host} "cd ${target_dir} && pm2 start --name cli-$i ./cli -- --end 760 --work-dir work-$i --instance $i --num-instances 4 --output /mnt/volume_ams3_01/video"
done

host=134.209.94.160
for i in {0..3}
do
  ssh ${user}@${host} "cd ${target_dir} && pm2 start --name cli-$i ./cli -- --start 761 --work-dir work-$i --instance $i --num-instances 4 --output /mnt/volume_ams3_02/video"
done