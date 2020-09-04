#!/usr/bin/env python

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

import json
import cx_Oracle
import argparse  
import traceback
from prettytable import PrettyTable
import logging
import dadEdit3_config
import dadEdit3_utils
from dadEdit3_utils import logger

def get_services(connection, args):
    cursor = connection.cursor()
    query = 'select id, name,  context_root,  type, clean, frozen, cluster_name, entity, frontend_entity, ' \
            'application_name, redeploy, config_refresh '
    binding = {}
    if args.detailed:
        query += ', ords_version, p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, path, tpl_default, ' \
                 'tpl_mapping, tpl_plain, tpl_pu, tpl_al, tpl_rt, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20,' \
                 ' p21, p22, p23, p24, p25, p26, p27, p28, p29, p30, p31, p32, p33, p34, p35, p36, p37, p38, p39, p40'
    query += " from Service where 1=1"
    if args.service is not None and args.service:
        query += " and REGEXP_LIKE(name, :service_name, 'i')"
        binding['service_name'] = "(^" + "$|^".join(s.replace('%', '.*') for s in args.service) + "$)"
    if args.cluster is not None:
        query += " and UPPER(cluster_name) LIKE UPPER(:cluster_name) ESCAPE '\\'"
        binding['cluster_name'] = args.cluster.replace('_', '\\_')
    if args.entity is not None:
        query += " and UPPER(entity) LIKE UPPER(:entity) ESCAPE '\\'"
        binding['entity'] = args.entity.replace('_', '\\_')
    if args.frontend_entity is not None:
        query += " and UPPER(frontend_entity) LIKE UPPER(:frontend_entity) ESCAPE '\\'"
        binding['frontend_entity'] = args.frontend_entity.replace('_', '\\_')
    if args.id is not None:
        query += " and id = :id"
        binding['id'] = args.id
    query += " order by name"
    cursor.prepare(query)
    cursor.execute(None, binding)
    res = cursor.fetchall()
    services = []
    for r in res:
        services.append(dict(zip(tuple(cd[0].lower() for cd in cursor.description), r)))
    cursor.close()
    return services


def print_table(services, detailed=False):
    table = PrettyTable()
    if len(services) > 0:
        table.field_names = [services[0].keys()]
    for service in services:
        table.add_row(service.values())
    print(table)


def print_JSON(services):
    print('['),
    print(',\n'.join(map(lambda s: json.dumps(s), services))),
    print("]")


def get_parsed_arguments():
    parser = argparse.ArgumentParser()
    search_args = parser.add_argument_group('search arguments')
    search_args.add_argument('-s', '--service', type=str,
                             help='Name of the service. Ignores case. %% wildcard allowed', nargs='*')
    search_args.add_argument('-c', '--cluster', type=str, help='Name of the cluster. Ignores case. %% wildcard allowed')
    search_args.add_argument('-e', '--entity', type=str, help='Name of the entity. Ignores case. %% wildcard allowed')
    search_args.add_argument('-f', '--frontend_entity', type=str,
                             help='Name of the frontend entity. Ignores case.  %% wildcard allowed')
    search_args.add_argument('--id', type=int, help='Id of the service')

    parser.add_argument('-d', '--detailed', help='Gives detailed report of the services', action='store_true',
                        default=False)
    parser.add_argument('-t', '--table', help='Presents the data in a table. JSON otherwise.', action='store_true',
                        default=False)
    parser.add_argument('--debug', help='Debug level of logging', action='store_true', default=False)
    # When arguments syntax is incorrect OR when user write -h, an exception is thrown.
    try:
        return parser.parse_args()
    except argparse.ArgumentError:
        parser.exit(status=2)


def main():
    args = get_parsed_arguments()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    con = dadEdit3_utils.connect_to_database()
    services = get_services(con, args)
    if args.table:
        print_table(services, args.detailed)
    else:
        print_JSON(services)
    dadEdit3_utils.disconnect_from_database(con)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        exit(e.code)
    except:
        logger.error(traceback.format_exc())
        exit(1)
