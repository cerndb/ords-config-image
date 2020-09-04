#!/usr/bin/env python

#    Copyright 2020 CERN
#   This software is distributed under the terms of the GNU General Public Licence
#   version 3 (GPL Version 3), copied verbatim in the file "COPYING". In applying	
#   this licence, CERN does not waive the privileges and immunities granted to it	
#   by virtue of its status as an Intergovernmental Organization or submit itself	
#   to any jurisdiction.

import collections
import itertools
from dadEdit3_utils import logger


def get_service(connection, service_name):
    logger.info('Retrieving service %s' %service_name)
    cursor = connection.cursor()
    cursor.prepare('select * from Service where name = :service_name')
    cursor.execute(None, {'service_name': service_name})
    res = cursor.fetchone()
    resultDict = dict(zip(tuple(cd[0].lower() for cd in cursor.description), res))
    cursor.close()
    logger.info('Service retrieved')
    return resultDict


def get_dads(connection, service_name, active=True):
    logger.info('Retrieving all DADs of the service %s with state active==%s' % (service_name, active))
    service = get_service(connection, service_name)
    if not service:
        logger.error("A service called %s could not be retrieved." % service_name)
        return []
    cur = connection.cursor()
    cur.prepare('select * from Dad where service_id = :s_id and active = :active order by id')
    cur.execute(None, {'s_id': service['id'], 'active': 'Y' if active else 'N'}) 
    res = cur.fetchall()
    dads = []
    for r in res:
        dads.append(dict(zip(tuple(cd[0].lower() for cd in cur.description), r)))
    cur.close()
    logger.info('DADs retrieved')
    return dads

def remove_password(schema_id):
    raise NotImplementedError



def get_schemas(connection, dad_id):
    cur = connection.cursor()
    cur.prepare('select Sch.id as schema_id, Sch.name as schema_name, ENCRYPTION_FUNCTIONS.get_pass_decrypted(Sch.id) as password, Sch.type as schema_type, Sch.dad_id, D.name as dad_name, D.database as database, D.* \
    from Schema_table Sch \
    JOIN Dad D \
    ON Sch.dad_id = D.id \
    where Sch.dad_id = :d_id \
    order by Sch.id')
    cur.execute(None, {'d_id': dad_id})
    res = cur.fetchall()
    schemas = []
    for r in res:
        schemas.append(dict(zip(tuple(cd[0].lower() for cd in cur.description), r)))
    cur.close()
    return schemas


def get_parameters_esthetic_relations(connection):
    logger.info('Retrieving information in Relation_between_column_names table.')
    cur = connection.cursor()
    cur.execute('select internal_name, esthetic_name from Relation_between_column_names order by internal_name')
    res = cur.fetchall()
    cur.close()
    logger.info('Information in Relation_between_column_names table retrieved.')
    return dict(res) # since there are only 2 values, this dirty trick can be used
