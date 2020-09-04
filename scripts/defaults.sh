#!/bin/bash

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

export TBAG_SERVICE_ACCOUNT_TAG=${TBAG_SERVICE_ACCOUNT_TAG:-'jeedy-service/serviceaccounts.dbjeedy_pwd'}
export TNS_ADMIN=${TNS_ADMIN:-"/ORA/dbs01/syscontrol/etc"}
export TNSNAMES_URL=${TNSNAMES_URL:-"http://service-oracle-tnsnames.web.cern.ch/service-oracle-tnsnames/tnsnames.ora"}
export VOLUME_MOUNT_DIRECTORY=${VOLUME_MOUNT_DIRECTORY:-"/ORA/dbs01/syscontrol/local/dadEdit"}
export TBAG_ACCOUNT_NAME=${TBAG_ACCOUNT_NAME:-'dbjeedy'}
export TBAG_PASSWORD_TAGS=${TBAG_PASSWORD_TAGS:-"serviceaccounts.dadedit_pwd"}
export TBAG_ACCOUNT_PASS=${TBAG_ACCOUNT_PASS:-""}
export TBAG_SECRETS_FILE_FILENAME_FULL_PATH=${TBAG_SECRETS_FILE_FILENAME_FULL_PATH:-"/ORA/dbs01/syscontrol/projects/systools/etc/passwd.dadedit"}
export TARGET_CONFIG_OWNER=${TARGET_CONFIG_OWNER:="1000:1000"}
export DAD_EDIT3_DB_PASSWORD=${DAD_EDIT3_DB_PASSWORD:-""}
export TBAG_SERVICE=${TBAG_SERVICE:-"jeedy-service"}
export DEV_DADEDIT_DB=${DEV_DADEDIT_DB:-"false"}
export TBAG_TIMEOUT=${TBAG_TIMEOUT:-"20"}
if [ "${DEV_DADEDIT_DB}" = "false" ]; then 
export TBAG_PASSWORD_TAGS=${TBAG_PASSWORD_TAGS:-"serviceaccounts.dadedit_pwd"}
else
export TBAG_PASSWORD_TAGS=${TBAG_PASSWORD_TAGS:-"serviceaccounts.dadedit_dev_pwd"}
fi