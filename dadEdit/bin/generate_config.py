#!/usr/bin/env python

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

import cx_Oracle
from jinja2 import Environment, Template, FileSystemLoader;
import argparse 
import sys, os
from datetime import datetime
import traceback
from dadEdit3_utils import connect_to_database, disconnect_from_database, logger
import database_queries
import dadEdit3_config
import dadEdit3_utils
import itertools
import re
import logging
import xml.etree.ElementTree as ET
import subprocess
import shutil


def generate_dictionary_for_template(parameters, relations):
    result = dict()
    for index, elem in enumerate(parameters):
        parameter_name = 'p%s' % (index+1)
        if parameters[elem] is not None and parameter_name in relations:
            esthetic_name = relations[parameter_name]
            result[esthetic_name] = parameters[elem]
    return result


def write_template(template_name, template_output):
    f = open(template_name, 'w')
    f.write(template_output)
    f.close()
    logger.debug('Template %s rendered and saved.' % template_name)


def check_service(service, args):
    logger.info('Checking service')
    logger.debug('\tforceClean: %s' % args.forceClean)
    logger.debug('\tforceFrozen: %s' % args.forceFrozen)
    if not service: 
        return 'Service passed by parameter does not exist.'
    if (service['clean'] == 'Y' and not args.forceClean) or (service['frozen'] == 'Y' and not args.forceFrozen):
        return 'Service passed by parameter is frozen or clean and forceClean/forceFrozen flags are disabled'
    if service['context_root'] is None:
        return 'Context_root is null.'
    logger.info('Checking if all mandatory parameters exist.')
    logger.info('Mandatory parameters: ords_version, context_root, application_name, type and path')
    for parameter_name in ['ords_version','context_root','application_name','type','path']:
        if service[parameter_name] is None:
            return 'Parameter %s is not defined' % service[parameter_name]
    logger.info('All mandatory parameters exist.')

    logger.info('The service check finished successfully')


def check_artifacts_directory(service):
    if os.path.isfile(service['path']):
        return '%s is a regular file.' % service['path']
    logger.info('Creating %s' % service['path'])
    try:
        os.makedirs(service['path']) 
    except OSError as e:
        if e.errno == 13: # 13 -> Permission denied.
            return 'Permission denied: You cannot create %s' % service['path']
    if not os.access(service['path'], os.W_OK):
        return 'Permission denied: You cannot write inside %s' % service['path']
    logger.info('%s created.' % service['path'])


def check_templates(service):
    logger.info('Checking if \'templates\' fields are not null and if \'templates\' files exist.')
    for template in ['tpl_default', 'tpl_mapping', 'tpl_plain', 'tpl_pu', 'tpl_al', 'tpl_rt']:
        if template not in service:
            return 'Template field: %s is not defined.' % template
        if not os.path.isfile(dadEdit3_config.templates_directory + service[template]):
            return 'Template file: %s%s does not exist for %s' % (dadEdit3_config.templates_directory, service[template], template )
    logger.info('Template file are defined and exist.')


def check_parameters(service, args, con):
    for error in [check_service(service, args), check_artifacts_directory(service), check_templates(service)]:
        if error is not None:
            logger.error('There was an error checking the setup: %s' % error)
            disconnect_from_database(con)
            exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    requiredArgs = parser.add_argument_group('required arguments')
    requiredArgs.add_argument('-s', '--service', type=str, help='Name of Service', required=True)
    parser.add_argument('-fc', '--forceClean', help='Ignore Clean flag.', action='store_true', default=False)
    parser.add_argument('-ff', '--forceFrozen', help='Ignore Frozen flag.', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', help='Log everything', action='store_true', default=False)
    try:
        args = parser.parse_args()
    except:
        parser.exit(status=2)
    return args


def write_schema_template(schema,service,relations,env):
    schema_type_lower  = schema['schema_type'].lower()
    logger.debug('Rendering and saving \'schema\' (schema \'%s\').' % schema['id'])
    schema_template = env.get_template(service['tpl_' + schema_type_lower]) 
    parameters = dict(filter(lambda elem: re.match('^p\d+$', elem[0]), schema.items()))
    esthetic_parameters = generate_dictionary_for_template(parameters,relations)
    schema_template_output = schema_template.render(sch=schema, service=service, final_parameters=esthetic_parameters)
    schema_name = schema['dad_name'] + (('_' + schema_type_lower) if not schema_type_lower == 'plain' else '') + '.xml'
    write_template(schema_name, schema_template_output)
    logger.debug('Schema rendered and saved successfully (schema \'%s\').' % schema['id'])

def replace_db_password_with_tbag(sch):
    tbag_key = '%s.%s.%s' % (sch['database'], sch['schema_name'], sch['schema_type'])
    password_from_tbag = dadEdit3_utils.get_password_from_tbag(tbag_key)
    if password_from_tbag is not None:
        sch['password'] = password_from_tbag
    else:
        logger.warning("Password %s couldnt be retrieved from tbag. Using the one saved in DB (%s)." % (tbag_key, sch['password']))

def write_schemas_templates(active_schemas,service,relations,env):
    for sch in active_schemas:
        replace_db_password_with_tbag(sch)
        schema_type_lower = sch['schema_type'].lower()
        if schema_type_lower not in ['plain', 'pu', 'al', 'rt']:
            logger.warn('Type ( %s ) of schema %s is not supported. It will be skipped' % (sch['type'], sch['name']))
        else:
            write_schema_template(sch,service,relations, env)


def write_defaults_template(service, relations, env):
    logger.debug('Rendering and saving \'defaults\' template')
    defaults_template = env.get_template(service['tpl_default']) 
    time_now = datetime.now().strftime('%a %b %d %H:%M:%S CEST %Y')
    parameters = dict(filter(lambda elem: re.match('^p\d+$',elem[0]), service.items()))  # take only p1, p2...p2137...
    esthetic_parameters = generate_dictionary_for_template(parameters, relations)
    write_template('defaults.xml', defaults_template.render(final_parameters=esthetic_parameters, time_now=time_now))
    logger.debug('Defaults template rendered and saved successfully')


def write_url_mapping_template(service, active_dads, env):
    logger.debug('Rendering and saving \'url_mapping\' template')
    url_mapping_template = env.get_template(service['tpl_mapping'])
    write_template('url-mapping.xml', url_mapping_template.render(listOfDads=active_dads, service=service))
    logger.debug('Url-mapping template rendered and saved successfully')


def get_jinja_environment():
    logger.debug('Creating jinja2 environment.')
    templateLoader = FileSystemLoader(searchpath = dadEdit3_config.templates_directory)
    env = Environment(loader = templateLoader)
    logger.debug('Jinja2 environment created.')
    return env


def create_conf_dir(path):
    os.chdir(path)
    if not os.path.exists('./conf'):
        logger.info('Creating \'conf\' folder.')
        os.makedirs('conf')
        logger.info('\'conf\' folder created.')
    os.chdir('./conf') 
    logger.info('The conf directory is %s' % os.getcwd())
 

def replace_configdir(configdir, web_template_dir):
    os.chdir(web_template_dir)
    logger.info('Reading content of web.xml.')
    web_xml_content = ET.parse('web.xml')
    root = web_xml_content.getroot()
    logger.info('Replacing content of web.xml.')
    ns = 'http://java.sun.com/xml/ns/j2ee'
    ET.register_namespace('',ns)
    for param in root.findall('{%s}context-param' % ns):
        param_name = param.find('{%s}param-name' % ns)
        param_value = param.find('{%s}param-value' % ns)
        if param_name.text == 'config.dir':
            param_value.text = configdir
    web_xml_content.write('web.xml')
    logger.info('configdir of web.xml replaced.')
  

def update_war(result_folder, war_name): #FIXME: replace with python's  zipfile, excluding war files from the archive
    os.chdir(result_folder)
    zipResult = subprocess.call(['zip', '-r', war_name, '.']) 
    if zipResult == 0:
        logger.info('War updated. Status: %s.' % zipResult)
    else:
        logger.error('zip not updated. Status: %s.' % zipResult)
        exit(1)


def pack_war(service,result_war_filename,targer_conf_dir,result_dir=dadEdit3_config.result_wars_directory,):
    source_web_template_dir = '%sords_templates/%s/%s/%s' % (dadEdit3_config.templates_directory, service['type'].lower(), service['ords_version'],'WEB-INF')
    source_war_filename = 'ords-%s.war' % service['ords_version']
    result_war_file_fullpath = result_dir + result_war_filename
    source_war_file_fullpath = dadEdit3_config.source_war_files_directory + source_war_filename
    result_web_template_dir = result_dir+'WEB-INF'
    
    if not os.path.exists(source_web_template_dir) or not os.path.isdir(source_web_template_dir):
        if not os.path.exists(result_dir+'WEB-INF') or not os.path.isdir(result_dir+'WEB-INF'):
            logger.error('Template directory ' + source_web_template_dir + ' does not exist and it hasn\'t been moved already.')
            exit(1)
    if not os.path.exists(source_war_file_fullpath) or not os.path.isfile(source_war_file_fullpath):
            logger.error('ORDS war file ' + source_war_file_fullpath + ' does not exist. ')
            exit(1)
    shutil.copy2(source_war_file_fullpath, result_war_file_fullpath)
    if not os.path.exists(result_web_template_dir) or not os.path.isdir(result_web_template_dir):
        shutil.move(source_web_template_dir, result_dir) ## Due to copytree's poor absolute path management
    replace_configdir(targer_conf_dir,result_web_template_dir)
    update_war(result_dir,result_war_file_fullpath)


def main():
    args  = parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else: 
        logger.setLevel(logging.INFO)
    con = connect_to_database()
   
    service = database_queries.get_service(con, args.service)
    active_dads = database_queries.get_dads(con, service['name'], active=True)
    active_schemas = list(itertools.chain.from_iterable(list(map(lambda dad: database_queries.get_schemas(con, dad['id']), active_dads))))
    relations = database_queries.get_parameters_esthetic_relations(con)
    env = get_jinja_environment()
    container_conf_dir = dadEdit3_config.result_wars_directory
    target_conf_dir = service['path']
    os.makedirs(container_conf_dir,exist_ok=True)

    create_conf_dir(container_conf_dir)
    check_parameters(service, args, con)
    
    write_schemas_templates(active_schemas,service,relations,env)
    os.chdir('..')
    write_url_mapping_template(service, active_dads,env)
    write_defaults_template(service, relations, env)
    result_war_filename = 'ords-%s' % service['name']

    os.makedirs(target_conf_dir,exist_ok=True)
    os.symlink(container_conf_dir,target_conf_dir+'/'+result_war_filename,target_is_directory=True)
    pack_war(service,result_war_filename+'.war',target_conf_dir,container_conf_dir)

    disconnect_from_database(con)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        exit(e.code)
    except:
        logger.error("Other error: ")
        logger.error(traceback.format_exc())
        exit(1)
