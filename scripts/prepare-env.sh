#!/bin/bash

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

source /work-dir/scripts/defaults.sh

log (){
   echo $(date "+[%a %d-%b-%Y %H:%M:%S]") $1 >&2
}

if [ "${DEV_DADEDIT_DB}" != "false" ]; then
    sed -i 's/dadEdit3_schema = "dad_edit3"/dadEdit3_schema = "dad_edit3_dev"/' /work-dir/dadEdit/bin/dadEdit3_config.py
fi
## Get DadEdit3 database password
if [ -z "${TBAG_ACCOUNT_PASS}" ]; then ## get from teigi
    if [ ! -d /tmp/passwords ]; then 
        read -rsp "Enter TBAG_ACCOUNT_PASS password: " -t 20  TBAG_ACCOUNT_PASS
        if [ -z "${TBAG_ACCOUNT_PASS}" ]; then \
            log "No TBAG_ACCOUNT_PASS specified and there's nothing mounted in /tmp/passwords. Either specify
            the TBAG_ACCOUNT_PASS directly or provide a password for accessing teigi in /tmp/passwords."
            exit 2  
        fi
    else
        TBAG_ACCOUNT_PASS=$(get_passwd --password_directory /tmp/passwords "$TBAG_SERVICE_ACCOUNT_TAG")
        if [  $? != 0 ]; then
         log "The passsword for $TBAG_SERVICE_ACCOUNT_TAG has not been found. in /tmp/passwords. Exiting."
            exit 2  
        fi

    fi
     export TBAG_ACCOUNT_PASS
fi
/work-dir/scripts/teigi-download.sh 

if [ ! -f "$TNS_ADMIN/tnsnames.ora"  ]; then
    log "Downloading TNSNAMES from $TNSNAMES_URL"
    status_code=$(curl --write-out "%{http_code}" -sSL -o "$TNS_ADMIN/tnsnames.ora" "$TNSNAMES_URL")
if [ "$status_code" -lt 200 ] || [ "$status_code" -ge 400  ] ; then
        log "Error downloading TNSNAMES. Exiting."
        exit 2
    fi
fi

if [ -z "${SERVICE_NAME}" ]; then
    log "No SERVICE_NAME specified. Choose one of the following: $(/work-dir/dadEdit/bin/get_services.py | jq '.[] | .name'). Exiting"
    exit 2
fi

## Save all info about service in JSON file
services=(${SERVICE_NAME//,/ })
for service in "${services[@]}"
do
    /work-dir/dadEdit/bin/get_services.py --detailed -s "$service" > "${VOLUME_MOUNT_DIRECTORY}/service_info_${service}.json"
    if [  $? != 0 ]; then
        log "Error getting the services. Exiting."
        exit 2
    fi
done
# war_file_name=$(jq -r '.[] | "\(.application_name)-\(.ords_version).war"' "${VOLUME_MOUNT_DIRECTORY}/service_info_${SERVICE_NAME}.json")
# export war_file_name
##Check if the config dir set in the ORDS' web.xml is a subdirecory of volume mount directory. It can be changed in the dadEdit service
# if [[ ! $config_files_path =~ "${VOLUME_MOUNT_DIRECTORY}" ]]; then
#     log "The config ($config_files_path) directory is not a subdirectory of the VOLUME_MOUNT_DIRECTORY($VOLUME_MOUNT_DIRECTORY). 
#      The web.xml of the ords.war will be changed to set the config directory to $VOLUME_MOUNT_DIRECTORY/ords/config."
#     $war_file_path/$war_file_name sed -i 's#<param-value>CONFIGDIR</param-value>#<param-value>'"$VOLUME_MOUNT_DIRECTORY"'/ords/config</param-value>#' {} \;
# fi

