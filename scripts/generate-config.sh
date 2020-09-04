#!/bin/bash

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

source /work-dir/scripts/prepare-env.sh

cd /work-dir/dadEdit/bin || exit 1
services=(${SERVICE_NAME//,/ })

for service in "${services[@]}"
do
    if  ./generate_config.py -s "$service"  -ff -fc; then
        log "Config files generated"
    else
        log "Error generating config files"
        exit 2
    fi
done

war_file_path='/ORA/dbs01/syscontrol/local/dadEdit/wars' 
if [[ $SERVICE_NAME =~ , ]]; then
    ## Rename the war and move it to the mount directory
    if [ "${war_file_path}" != "${VOLUME_MOUNT_DIRECTORY}/wars" ]; then
        mv ${war_file_path}/*.war "${VOLUME_MOUNT_DIRECTORY}/wars/"
        log "Moved $("${war_file_path}/*.war") to ${VOLUME_MOUNT_DIRECTORY}/wars/"
    fi
else
    mv ${war_file_path}/*.war "${VOLUME_MOUNT_DIRECTORY}/wars/ords.war"
    log "Moved $("${war_file_path}/*.war") to ${VOLUME_MOUNT_DIRECTORY}/wars/ords.war" 
fi

chown -R "$TARGET_CONFIG_OWNER" "$VOLUME_MOUNT_DIRECTORY"
chmod a+rwX -R "$VOLUME_MOUNT_DIRECTORY"

mkdir /work-dir/artifacts
ln -s "$VOLUME_MOUNT_DIRECTORY" /work-dir/artifacts/ords
cd /work-dir/ || return