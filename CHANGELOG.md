# Changelog 

# 3.4 - 02.09.2020
Stop using database-stored passwords, take the passwords directly from teigi.

## 3.3 - 20.08.2020
Fix schema template to accept parameters

## 3.2 - 14.08.2020
Add ords war version: 20.2.0.178.1804

## 3.1 - 21.07.2020
Remove the override of configdir

## 3.0 - 20.07.2020
Added CI testing of the produced artifacts

## 2.9 - 17.07.2020
Removed the override of the tnsnames location in config files

## 2.8 - 13.07.2020
- Added possibility to produce multiple WARs. The service names passed should be comma separated, without spaces
- The config directory is replaced with `/srv/tomcat/webapps`. This allows us to deploy in any context. In future the configdir will be changed in dadEdit service and no longer hardcoded.
- Define default for 'db.invalidPoolTimeout': '15m'

## 2.7 - 19.06.2020
- Fixed logging for pack_war script
- Now requiring tbag password instead of db, since tbag is needed at later stage anyway

## 2.6 - 11.06.2020
- Imported and modified scripts from https://gitlab.cern.ch/db/cerndb-infra-apps/tree/master/dadEdit3/bin
- Imported and modified templates from:
https://gitlab.cern.ch/db/cerndb-infra-apps/-/tree/master/dadEdit3/etc
- Imported wars from:
https://gitlab.cern.ch/db/cerndb-sw-ords/-/tree/master/ords/wars
- Moved to python 3.6
- The templatess parameters are not "hardcoded" - can be added in the dadEdit application
- Secrets are taken from tegi, if available

## 2.5 - 28.05.2020
Change defualt TNSNames location

## 2.4
Change the port for tbag

## 2.3 
If no password is given, the user is asked for it at startup

## 2.2 
- Added possibility to use this image for ORDS management
- Removed APEX images
- Remove APEX images redirects

## 2.1 
Remove images fallback

## 2.0
Introduced images fallback for the APEX images redirect

## 1.8
Manage the APEX images locally

## 1.7
 Ovewrtie the templates

## 1.6
Disable debug mode 

## 1.5 
 Move the redirect src location not to be overrident by the volume mount 

## 1.4
Refactor

## 1.3
Redirect the requests for images to apex.cern.ch

## 1.2
Rename the resulting war to ORDS.war

## 1.1
Mount the dbjeedy password as a file for get_passwd to read

## 1.0 
 Update CERNDB_BASE_IMAGE_TAG