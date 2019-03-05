#!/bin/bash
curl --user "$USER" --digest --request GET "https://cloud.mongodb.com/api/atlas/v1.0/groups/"$PROJECT"/clusters/"$SERVER"-shard-00-00-zxuwk.mongodb.net/logs/mongodb.gz"  --output "mongodb0.gz"
curl --user "$USER" --digest --request GET "https://cloud.mongodb.com/api/atlas/v1.0/groups/"$PROJECT"/clusters/"$SERVER"-shard-00-01-zxuwk.mongodb.net/logs/mongodb.gz"  --output "mongodb1.gz"
curl --user "$USER" --digest --request GET "https://cloud.mongodb.com/api/atlas/v1.0/groups/"$PROJECT"/clusters/"$SERVER"-shard-00-02-zxuwk.mongodb.net/logs/mongodb.gz"  --output "mongodb2.gz"
gunzip mongodb0.gz
gunzip mongodb1.gz
gunzip mongodb2.gz
mlogfilter mongodb0 --slow 1 > "/app/mongodb0_filter.log"
if [ -s /app/mongodb0_filter.log ]
then
    mloginfo mongodb0_filter.log --queries --sort sum > "/app/output/slow_log_rank0.txt"
else
    echo "mongodb0_filter.log is empty."
fi

mlogfilter mongodb1 --slow 1 > "/app/mongodb1_filter.log"
if [ -s /app/mongodb1_filter.log ]
then
    mloginfo mongodb1_filter.log --queries --sort sum > "/app/output/slow_log_rank1.txt"
else
    echo "mongodb1_filter.log is empty."
fi

mlogfilter mongodb2 --slow 1 > "/app/mongodb2_filter.log"
if [ -s /app/mongodb2_filter.log ]
then
    mloginfo mongodb2_filter.log --queries --sort sum > "/app/output/slow_log_rank2.txt"
else
    echo "mongodb2_filter.log is empty."
fi
echo Running python now...
python send_email.py $SERVER
echo Task complete