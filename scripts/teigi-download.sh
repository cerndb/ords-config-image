#!/bin/bash

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

: '
This script is meant to be run **inside a Docker container**. Please do NOT use in 
any other case (especially with root privileges) because it will attemp to empty
files, append to files, change ownership of directories etc.


REQUIRED environment variables that need to be set:
- TBAG_ACCOUNT_PASS                     --> The password of the user specified above.
- TBAG_SECRETS_FILE_FILENAME_FULL_PATH  --> The full path of the file that will be created, containing the requested secrets.
                                             Please avoid using common Linux filesystem locations, as this may destroy your fs.
- TBAG_PASSWORD_TAGS                    --> The password tags/keys to retrieve from the Secrets Manager Backend.
                                             If we want to retrieve multiple tags/keys, they should be comma seperated (e.g. "tag1,tag2,tag3")
Note: The credentials that will be provided above will be used to perform kinit and get a valid Kerberos ticket.


 OPTIONAL environment variables:
- TBAG_ACCOUNT_NAME: The user that will be able to query the Secrets Manager Backend (e.g. Teigi). Defaults to dbjeedy
- TBAG_SERVICE: The service to query in Teigi. Defaults to "jeedy-service".
'

set -e

RED_COLOR="\033[0;31m"
GREEN_COLOR="\033[0;32m"
NO_COLOR="\033[0m"


function on_exit() {
    echo -e "${RED_COLOR}[ERROR] Error on line ${1}.${NO_COLOR}"
    exit 1
}


function show_error_and_exit() {
    echo -e "${RED_COLOR}${1}${NO_COLOR}"
    exit 1
}


function show_success_message() {
    echo -e "${GREEN_COLOR}${1}${NO_COLOR}"
}


# Check if the required tools are installed at the system
function check_required_tools() {
    REQUIRED_TOOLS=(
        kinit   \  # used to get a valid Kerberos ticket
        printf  \  # used to format the output from Teigi before appending it to the password file
        python  \  # used to format the output from Teigi before appending it to the password file
        tbag    \  # tool provided by the CERN AI team to query Teigi
        curl      # (WAS) used to query the API of the Secret Manager backend
    )

    missing_tool_found=0
    for tool in ${REQUIRED_TOOLS[@]}; do
        if ! command -v ${tool} &> /dev/null; then
            echo -e "${RED_COLOR}[ERROR] The required tool '$tool' is not installed on this system!${NO_COLOR}"
            missing_tool_found=1
        fi
    done

    if [ "$missing_tool_found" -eq 1 ]; then
        show_error_and_exit "[ERROR] Please install the required tools before proceeding further!"
    fi

    show_success_message "[INFO] All the required tools are installed in the system."
}


# Check if the required environment variables exist
function check_required_env_variables() {
    : "${TBAG_ACCOUNT_NAME?You need to specify the account name that is able to download the requested passwords.}"
    : "${TBAG_ACCOUNT_PASS?You need to specify the account password for downloading the requested passwords.}"
    
    # The 'TBAG_SECRETS_FILE_FILENAME_FULL_PATH' environment variable is made mandatory because if you mount a volume in Kubernetes
    # in a specifc location (and we use with initContainers), the generated file should be created under a volume's path.
    : "${TBAG_SECRETS_FILE_FILENAME_FULL_PATH?You need to specify the location that the generated file will created at.}"

    : "${TBAG_PASSWORD_TAGS?You need to specify the password tag(s) to retrieve.}"
    show_success_message "[INFO] All the required environment variables have been set."
}


# Execute kinit for the specified user
function execute_kinit() {
    echo "${TBAG_ACCOUNT_PASS}" | kinit ${TBAG_ACCOUNT_NAME}@CERN.CH
    if [ $? -eq 0 ]; then
        show_success_message "[INFO] The 'kinit' command was executed successfully."
    fi
}


# Retrieve the specified secrets from Teigi and create all the necessary
# files, if the response to the Secret Manager backend is successful.
function retrieve_all_password_from_teigi() {
    mkdir_output=$(mkdir -p $(dirname ${TBAG_SECRETS_FILE_FILENAME_FULL_PATH}))

    # we'll save Teigi's response in a temporary file
    temp_output_file="/tmp/temp-teigi-output"

    # Empty the file that we want to save the passwords, otherwise if the specified file
    # already exists in the filesystem with random contents, the get_passwd script, that
    # may be used, could fail.
    > ${TBAG_SECRETS_FILE_FILENAME_FULL_PATH}

    for tag in ${TBAG_PASSWORD_TAGS//,/ }; do

        > ${temp_output_file}
        set +e
        echo "[INFO] Retrieving the '${tag}' tag from the '${TBAG_SERVICE}' service"
        tbag --pdb-timeout ${TBAG_TIMEOUT} show --service ${TBAG_SERVICE} --file ${temp_output_file} ${tag} > /dev/null 2>&1
        if [ ! $? -eq 0 ] || [ ! -s ${temp_output_file} ] || [ ! -f ${temp_output_file} ]; then
            show_error_and_exit "[ERROR] Could not retrieve the '${tag}' tag from the '${TBAG_SERVICE}' service."
        fi

        # IMPROVE: Create Regex patterns for some of the use cases below.

        # if the temporary file has 2 lines or more
        if [ $(wc -l <$(realpath ${temp_output_file})) -ge 2 ]; then

            # For every line of the temporary output file, check only the uncommented lines.
            # If these lines contain the string "TAG" they will be appended to the final generated file.
            # Otherwise, the script will exit with an error message.

            while IFS="" read -r line || [ -n "${line}" ]; do
                # If line is a comment or empty then continue
                if [[ "${line}" =~ \#.*$ ]] || [ -z "${line}" ];then continue; fi

                grep_output=$(echo ${line} | grep "TAG")
                if [ $? -eq 0 ]; then
                    echo ${line} >> ${TBAG_SECRETS_FILE_FILENAME_FULL_PATH}
                else
                    show_error_and_exit "[ERROR] The tag '${tag}', on the '${TBAG_SERVICE}' service, doesn't have a valid format ."
                fi
            done < ${temp_output_file}

        # if the temporary file has less than two lines
        else
            # check if the retrieved secret from Teigi contains the string "TAG"
            contains_tag_string=$(cat ${temp_output_file} | grep "TAG")
            if [ $? -eq 0 ]; then
                cat ${temp_output_file} >> ${TBAG_SECRETS_FILE_FILENAME_FULL_PATH}
            else
                printf 'TAG %s=%s\n' ${tag} $(cat ${temp_output_file}) >> ${TBAG_SECRETS_FILE_FILENAME_FULL_PATH}
            fi
        fi

        set -e
        
        rm -rf ${temp_output_file}
    done

    show_success_message "[INFO] All passwords were retrieved successfully from TEIGI. You can view the generated file under: '${TBAG_SECRETS_FILE_FILENAME_FULL_PATH}'"
}


# Change the ownership of the (mounted) directory that contains the password file
function change_mounted_dir_ownership() {
    mounted_dir_name=$(dirname ${TBAG_SECRETS_FILE_FILENAME_FULL_PATH});
    chown -R $TARGET_CONFIG_OWNER ${mounted_dir_name}
}


function main() {
    trap 'on_exit $LINENO' ERR
    check_required_env_variables
    check_required_tools
    execute_kinit
    retrieve_all_password_from_teigi
    change_mounted_dir_ownership
}


if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

