#!/bin/bash

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

if [[ $TARGET_IMAGE_TAG ]]; then
   echo "[INFO] Used image tag: $TARGET_IMAGE_TAG"
fi

printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' '*'
/work-dir/scripts/generate-config.sh
if [  $? == 0 ]; then
    services=(${SERVICE_NAME//,/ })
    for service in "${services[@]}"
    do
        echo "* Service: $service"
        echo "* Successfully generated ords.war and config files."
        echo "* ORDS version: $(jq -r '.[] | .ords_version' "/ORA/dbs01/syscontrol/local/dadEdit/service_info_${service}.json")"
        echo "* Application name: $(jq -r '.[] | .application_name' "/ORA/dbs01/syscontrol/local/dadEdit/service_info_${service}.json")"
    done
    echo "* For more information and examples of usage see /work-dir/README"
else 
    echo "* Something went wrong. You might want to see the guide in /work-dir/README"
fi
    printf '%*s\n' "${COLUMNS:-$(tput cols)}" '' | tr ' ' '*'

exec "$@"