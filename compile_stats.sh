#!/bin/bash

STAT_FOLDER=/tmp/kannel_stats
KANNEL_LOGS_FOLDER=/var/log/kannel
OUTPUT_FILE=/var/www/stats/index.html
USAGE_SCRIPT=/var/lib/couchdb/smpp2local/kannel_usage.py

rm -rf ${STAT_FOLDER}
mkdir -p ${STAT_FOLDER}

cp ${KANNEL_LOGS_FOLDER}/access.log* ${STAT_FOLDER}
cd ${STAT_FOLDER} && gunzip *.gz && cat access.log* > all_access.log

${USAGE_SCRIPT} --html ${STAT_FOLDER}/all_access.log > ${OUTPUT_FILE}