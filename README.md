# ords-config-image
This image generates configuration files and war files for Oracle Rest DataServices based on data provided by dadEdit3
[[_TOC_]]
## ORDS Managment Quickstart
Here's how to manage ORDS installations in 5 simple steps:
1. SSH into dbadm
```
ssh dbadm
```
2. Retrieve the DadEdit3 database password. Copy it.
```
get_passwd password_dadedit3_cerndb1
```
3. From your machine, run the docker container, specifying the service you want to manage (APEX, ORAWEB, ORDS, APEX-SSO, ORAWEB-SSO... - for a full list run the container without specifying the service):
```
 docker run --rm -it -e SERVICE_NAME=ORDS gitlab-registry.cern.ch/jeedy/utils/ords-config-image:2.3 /bin/bash
```
4. You will be asked for dadEdit3 database password. Paste the password.

5. Et voilà! Now you should be able to [interact with ORDS](#interacting-with-ords) and execute the commands from the [examples section](#example-commands). There's also a README in the main directory of the container (`/work-dir/`).


## Detailed How-To
### Required setup
To generate the config and the war file, run the container with following environment variables set:

1. **SERVICE_NAME** to the service for which the config should be generated

2. **password for dbjeedy service account** should be mounted in /tmp/passwords in a file formatted like so:
`TAG jeedy-service/serviceaccounts.dbjeedy_pwd=XXXXX`. Other account can be used using the TBAG_ACCOUNT_NAME and TBAG_SERVICE_ACCOUNT_TAG variables.

**OR**

1. **SERVICE_NAME** to the service for which the config should be generated

2. **TBAG_ACCOUNT_PASS** - The passsword to access the teigi database can be specified directly through this environment variable if working in a trusted environment. Otherwise **this can be omitted** and you will be asked to enter it during container startup.

### Optional env variables:
<table>
    <tr>
        <th><b>Name</b></th>
        <th><b>Description</b></th>
        <th><b>Default</b></th>
    </tr>
    <tr>
        <td>
            <b>TBAG_SERVICE_ACCOUNT_TAG</b> 
        </td>
        <td>
            TAG used for the service account password
        </td>
        <td style="text-align:center">
            jeedy-service/serviceaccounts.dbjeedy_pwd
        </td>
    </tr>
     <tr>
        <td>
            <b>TBAG_TIMEOUT</b> 
        </td>
        <td>
            Timeout for the teigi client in seconds. Only integers.
        </td>
        <td style="text-align:center">
            20
        </td>
    </tr>
    <tr>
        <td>
            <b>TNS_ADMIN</b> 
        </td>
        <td>
            location of the TNS names file in this dockerfile, if mounted from outside
        </td>
        <td style="text-align:center">
            /ORA/dbs01/syscontrol/etc
        </td>
    </tr>
    <tr>
        <td>
            <b>TNSNAMES_URL</b> 
        </td>
        <td>
            URL from which the TNS names will be downloaded
        </td>
        <td style="text-align:center">
            http://service-oracle-tnsnames.web.cern.ch/service-oracle-tnsnames/tnsnames.ora
        </td>
    </tr>
    <tr>
        <td>
            <b>TBAG_ACCOUNT_NAME</b> 
        </td>
        <td>
            The user that will be able to query the Secrets Manager Backend (e.g. Teigi).
        </td>
        <td style="text-align:center">
            dbjeedy
        </td>
    </tr>
    </tr>
    <tr>
        <td>
            <b>TBAG_PASSWORD_TAGS</b> 
        </td>
        <td>
            The password tags/keys to retrieve from the Secrets Manager Backend.
                                             If we want to retrieve multiple tags/keys, they should be comma seperated (e.g. "tag1,tag2,tag3")
        </td>
        <td style="text-align:center">
            serviceaccounts.dadedit_pwd
        </td>
    </tr>
    </tr>
    <tr>
        <td>
            <b>TBAG_SECRETS_FILE_FILENAME_FULL_PATH</b> 
        </td>
        <td>
            The full path of the file that will be created, containing the requested secrets.
                                             Please avoid using common Linux filesystem locations, as this may destroy your fs.
        </td>
        <td style="text-align:center">
            /ORA/dbs01/syscontrol/projects/systools/etc/passwd.dadedit
        </td>
    </tr>
  <tr>
        <td>
            <b>TBAG_SERVICE</b> 
        </td>
        <td>
           The service to query in Teigi
        </td>
        <td style="text-align:center">
            jeedy-service
        </td>
    </tr>
  <tr>
        <td>
            <b>TARGET_CONTAINER_USER</b> 
        </td>
        <td>
           The user (name or id) to change the ownership of the created file(s)
        </td>
        <td style="text-align:center">
            1000
        </td>
    </tr>
  <tr>
        <td>
            <b>TARGET_CONTAINER_GROUP</b> 
        </td>
        <td>
           The group (name or id) to change the ownership of the created file(s)
        </td>
        <td style="text-align:center">
            1000
        </td>
    </tr>
    <tr>
        <td>
            <b>VOLUME_MOUNT_DIRECTORY</b> 
        </td>
        <td>
            If you want to change the default location of generated files. It has to correspond to the config directory set in ORDS' properties (through the dadEdit3 service).
        </td>
        <td style="text-align:center">
            /ORA/dbs01/syscontrol/local/dadEdit
        </td>
    </tr>
</table>

### Other
It's best to run this Docker image from inside of the CERN network.

## Artifacts
If creating the artifacts succeeded, there should be a directory (in `/ORA/dbs01/syscontrol/local/dadEdit` by default) with 3 key elements:
1. `conf` directory, containing all of the configuration files for ORDS
2. `wars` directory, containing the preconfigured war (for SSO, non-SSO cases, pointing to the right config directory, etc.)
3. A JSON file, containing information about the service, taken from dadEdit3.

## Interacting with ORDS 
To display a full list of available commands, go to the directory or folder containing the ords.war file and execute the following command:

```
java -jar /work-dir/artifacts/ords/wars/ords.war help
```
A list of the available commands is displayed. To see instructions on how to use each of these commands, enter help followed by the command name, for example:
```
java -jar /work-dir/artifacts/ords/wars/ords.war help configdir
```

### Example commands
1. Validating the ORDS schema for `cerndb1`
```
java -jar /work-dir/artifacts/ords/wars/ords.war validate --database cerndb1
```
2. Change the default caching configuration to `disabled`
```
java -jar /work-dir/artifacts/ords/wars/ords.war set-property cache.caching true
```
3. Create or update an user named `ords_admin` with role `Listener Administrator`
```
java -jar /work-dir/artifacts/ords/wars/ords.war user ords_admin "Listener Administrator"
```
4.  Install or upgrade Oracle REST Data Services schema, proxy user and related database objects.
```
java -jar /work-dir/artifacts/ords/wars/ords.war schema
```

#### Validating the schemas
You can test all the schemas quickly by running script:
```
/ORA/dbs01/syscontrol/projects/dadEdit3/bin/test_all_schemas
```

__Watch out__ where you launch the script from! If you run it from a host which doesn't have access to the Technical Network, some of the DADs might appear incorrect in that case. 

## Using this image for retrieving the artifacts
Specify all the required parameters and the artifacts (WARs, config files) will be generated in `/ORA/dbs01/syscontrol/local/dadEdit` by default, so mount a volume there.
```
docker run --rm -v $PWD/passwd.jeedy_service_account:/tmp/passwords/passwd.jeedy_service_account -e SERVICE_NAME=DEVORDS -v $PWD/artifacts:/ORA/dbs01/syscontrol/local/dadEdit gitlab-registry.cern.ch/jeedy/utils/ords-config-image:2.3
```

## Getting DADs credentials
When the config files have been generated, it's possible to use the DAD information there to access the schemas.
If you navigate to `/work-dir/artifacts/ords/ords/<<SERVICE_NAME>>/ords/conf`, you can find the DAD configuration there.

If there's incosistency with the name of the DAD **config file name** with the **database name**, see the `url-mapping.xml` file in `/work-dir/artifacts/ords/ords/<<SERVICE_NAME>>/ords`.

_This image comes pre-installed with sqlplus for convenience._

## QA
### Q: How does ords.war know where the configuration files are?
A: In the `WEB-INF/web.xml` in ords.war there's a line specifying the config directory. It can be changed either manually (editing the web.xml and repacking) or we can let ORDS handle it - `java -jar /work-dir/artifacts/ords/wars/ords.war config <<new-path-to-config>>`

### Q: I just want to quickly test some new features/settings/bugs of ORDS locally, but against the exisiting DBs. How do I?
A: In that case you might want to try ORDS' standalone mode: `java -jar /work-dir/artifacts/ords/wars/ords.war standalone`

### Q: Wow, ORDS is so amazing, I want to know more and follow all the latest updates! Do you know any awesome resources?
A: Yes, see:
- [ThatJeffSmith](https://www.thatjeffsmith.com/oracle-rest-data-services-ords/)
- [Oracle-Base](https://oracle-base.com/articles/misc/articles-misc#ords)

