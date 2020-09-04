#!/usr/bin/env python

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

import logging
import subprocess
import traceback
from datetime import datetime
import cx_Oracle
import dadEdit3_config
import time
import json

logger = None

def getCurrentTime():
    return datetime.now().strftime('[%a %d-%b-%Y %H:%M:%S] ')


def get_logger(name=None):
    if logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.ERROR)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(formatter)
        _logger.addHandler(ch)
        return _logger
    return logger

logger=get_logger('logger')


def get_password(password_command_args):
    command = [dadEdit3_config.get_passwd_directory, password_command_args]
    p = subprocess.Popen(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    password, stderr = p.communicate()
    return password.decode("utf-8")


def get_connection_string():
    if hasattr(dadEdit3_config, 'dadEdit3_secret'):  # for local testing
        password_to_connect_to_database = dadEdit3_config.dadEdit3_secret
    else:
        password_to_connect_to_database = get_password(dadEdit3_config.dadEdit3_name_of_password_to_connect_to_database)
    if not password_to_connect_to_database:
        logger.error('Password_to_connect_to_database is empty.')
        exit(1)
    connection_information = dadEdit3_config.dadEdit3_schema + '/' + password_to_connect_to_database + '@' + dadEdit3_config.dadEdit3_database;
    return connection_information


def connect_to_database(connection_string=None):
    if connection_string is None:
        connection_string = get_connection_string()
    logger.info('Connecting to database.')
    try:
        con = cx_Oracle.connect(connection_string)
    except cx_Oracle.Error:
        logger.error(traceback.format_exc())
        logger.error('Connection to database NOT established.')
        exit(1)
    logger.info('Connection to database established.')
    return con


def disconnect_from_database(connection):
    logger.info('Disconnecting from the database.')
    try:
        connection.close()
    except cx_Oracle.Error:
        logger.error(traceback.format_exc())
        logger.error('Disconnecting failed.')
        exit(1)
    logger.info('Disconnected from the database.')

def get_password_from_tbag(password_tag, service="dadedit-service"):
    """Gets the password for the provided tag. Calls `tbag show`.
        Taken from jeedy-manager.
    Args:
        password_tag (str): The tag to look for and retrieve it's password.
        service (str): The service to look for the password_tag in.

    Returns:
        password (str): The password corresponding to the provided tag.
    """

    # where in the resulting tbag dict to look for the actual secret
    KEY_OF_SECRET_IN_TBAG_DICT = 'secret'

    tbag_show_command = 'tbag show --service %s %s' \
                        % (service, password_tag)

    # Max number of attempts to get secrets running 'tbag' in case of timeouts
    tbag_max_attempts = 3
    # Wait 2s between consecutive 'tbag' executions in case of timeouts
    tbag_wait_between_attempts = 2

    tbag_attempts_counter = 0
    tbag_success = False

    # Attempt to get secret from 'tbag' in a loop in case of timeouts
    while not tbag_success and tbag_attempts_counter < tbag_max_attempts:
        # References for below usage of subprocess:
        # - Stackoverflow: https://stackoverflow.com/a/35633457/3545896
        # - Docs: https://docs.python.org/2.7/library/subprocess.html#popen-constructor
        tbag_p = subprocess.Popen(tbag_show_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True)
        tbag_stdout, tbag_stderr = tbag_p.communicate()
        if tbag_p.returncode == 0:
            tbag_success = True
        else:
            if 'Connection timeout' in tbag_stderr:
                # Increment attempts counter and if limit not reached, try again
                tbag_attempts_counter += 1
                time.sleep(tbag_wait_between_attempts)
            else:
                logger.error('Could not get password for tag \'%s\'. Stderr from tbag: \'%s\'' % (password_tag, tbag_stderr.strip()))

    if not tbag_success:
        logger.error('Reached max number of attempts (%s) executing \'tbag\' to get secret tag \'%s\'.' % (tbag_max_attempts, password_tag))
        return
    # load JSON into Python dictionary
    tbag_response_json = tbag_stdout
    tbag_response_dict = json.loads(tbag_response_json)

    try:
        return tbag_response_dict[KEY_OF_SECRET_IN_TBAG_DICT]
    except KeyError:
        logger.error('Loaded tbag response dict did not not contain the expected key \'%s\'. '
                            'Not dumping dict as it potentially contains sensitive information' % KEY_OF_SECRET_IN_TBAG_DICT)


def set_password_in_tbag(secret_key,secret_value, service="dadedit-service"):
    """Sets the password for the provided tag. Calls `tbag show`.
        Taken from jeedy-manager.
    Args:
        password_tag (str): The tag to look for and retrieve it's password.
        service (str): The service to look for the password_tag in.
    """

    tbag_set_command = 'echo -n %s | tbag set --service %s %s' % (secret_value, service, secret_key)

    tbag_p = subprocess.Popen(tbag_set_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    _, tbag_stderr = tbag_p.communicate()
    if tbag_p.returncode != 0:
        logger.error("Could not create secret for the key '%s'. Stderr from tbag: '%s'" % (secret_key, tbag_stderr))
        return

    logger.info("Successfully created Teigi secret '%s'" % secret_key)
