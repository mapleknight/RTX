#!/usr/bin/python3

import os
import datetime
import json
import time
import re
from typing import Optional

from pygit2 import Repository, discover_repository


class RTXConfiguration:

    _GET_FILE_CMD = "scp araxconfig@araxconfig.rtx.ai:config_secrets.json "

    # ### Constructor
    def __init__(self):
        self.version = "ARAX 1.2.1"  # TODO: This probably shouldn't be hardcoded? What is it used for?

        # Grab instance/domain name info, if available
        file_dir = os.path.dirname(os.path.abspath(__file__))
        self.instance_name = '??'
        match = re.match(r'/mnt/data/orangeboard/(.+)/RTX/code', file_dir)
        if match:
            self.instance_name = match.group(1)
        if self.instance_name == 'production':
            self.instance_name = 'ARAX'

        try:
            with open(f"{file_dir}/config.domain") as infile:
                for line in infile:
                    self.domain = line.strip()
        except:
            self.domain = '??'

        # Determine the branch we're running in
        repo_path = discover_repository(file_dir)
        try:
            repo = Repository(repo_path)
            self.current_branch_name = repo.head.name.split("/")[-1]
        except Exception:
            # TODO: Figure out why Docker container doesn't like this Git branch determination method
            # Ok to skip branch name here for now since domain name can be used instead in such cases
            self.current_branch_name = None

        # Determine our maturity
        maturity_override_value = self._read_override_file(f"{file_dir}/maturity_override.txt")
        if maturity_override_value:
            self.maturity = maturity_override_value
        else:
            # Otherwise we'll dynamically determine our maturity based on instance/domain name and/or branch
            if self.domain in ["arax.ci.transltr.io", "kg2.ci.transltr.io", "Github actions ARAX test suite"]:
                self.maturity = "staging"
            elif self.domain in ["arax.test.transltr.io", "kg2.test.transltr.io"] or self.current_branch_name == "itrb-test":
                self.maturity = "testing"
            elif self.domain in ["arax.transltr.io", "kg2.transltr.io"] or self.current_branch_name == "production":
                self.maturity = "production"
            elif self.domain == "arax.ncats.io":
                if self.instance_name in ["ARAX", "kg2"] or self.current_branch_name == "production":
                    self.maturity = "production"
                else:
                    self.maturity = "development"
            else:
                self.maturity = "development"

        # Determine if this is an ITRB instance or our CICD instance
        self.is_itrb_instance = "transltr.io" in self.domain  # Hacky, but works

        config_secrets_file_path = os.path.dirname(os.path.abspath(__file__)) + '/config_secrets.json'
        config_dbs_file_path = os.path.dirname(os.path.abspath(__file__)) + '/config_dbs.json'
        config_secrets_local_file_path = os.path.dirname(os.path.abspath(__file__)) + '/config_secrets_local.json'

        # Download the latest copy of config_secrets.json as appropriate (or override by local file, if present)
        if os.path.exists(config_secrets_local_file_path):
            config_secrets_file_path = config_secrets_local_file_path
        elif not os.path.exists(config_secrets_file_path):
            # scp the file
            os.system(RTXConfiguration._GET_FILE_CMD + config_secrets_file_path)
        else:
            now_time = datetime.datetime.now()
            modified_time = time.localtime(os.stat(config_secrets_file_path).st_mtime)
            modified_time = datetime.datetime(*modified_time[:6])
            if (now_time - modified_time).days > 0:
                # scp the file
                os.system(RTXConfiguration._GET_FILE_CMD + config_secrets_file_path)

        # Load the contents of the two config files (config_dbs.json lives in the repo; no need to download)
        with open(config_secrets_file_path, 'r') as config_secrets_file:
            self.config_secrets = json.load(config_secrets_file)
        with open(config_dbs_file_path, 'r') as config_dbs_file:
            self.config_dbs = json.load(config_dbs_file)

        # AG: Not sure exactly what this is doing?
        self.is_production_server = False
        if ( ( 'HOSTNAME' in os.environ and os.environ['HOSTNAME'] == '6d6766e08a31' ) or
            ( 'PWD' in os.environ and 'mnt/data/orangeboard' in os.environ['PWD'] ) ):
            self.is_production_server = True

        # Set database file paths
        self.db_host = "arax.ncats.io"
        self.db_username = "rtxconfig"
        database_downloads = self.config_dbs["database_downloads"]
        self.cohd_database_path = database_downloads["cohd_database"]
        self.cohd_database_version = self.cohd_database_path.split('/')[-1].split('_v')[-1].replace('.db', '')
        self.graph_database_path = database_downloads["graph_database"]
        self.graph_database_version = self.graph_database_path.split('/')[-1].split('_v')[-1].replace('.sqlite', '')
        self.log_model_path = database_downloads["log_model"]
        self.log_model_version = self.log_model_path.split('/')[-1].split('_v')[-1].replace('.pkl', '')
        self.curie_to_pmids_path = database_downloads["curie_to_pmids"]
        self.curie_to_pmids_version = self.curie_to_pmids_path.split('/')[-1].split('_v')[-1].replace('.sqlite', '')
        self.node_synonymizer_path = database_downloads["node_synonymizer"]
        self.node_synonymizer_version = self.node_synonymizer_path.split('/')[-1].split('_v')[-1].replace('.sqlite', '')
        self.dtd_prob_path = database_downloads["dtd_prob"]
        self.dtd_prob_version = self.dtd_prob_path.split('/')[-1].split('_v')[-1].replace('.db', '')
        self.kg2c_sqlite_path = database_downloads["kg2c_sqlite"]
        self.kg2c_sqlite_version = self.kg2c_sqlite_path.split('/')[-1].split('_v')[-1].replace('.sqlite', '')
        self.kg2c_meta_kg_path = database_downloads["kg2c_meta_kg"]
        self.kg2c_meta_kg_version = self.kg2c_meta_kg_path.split('/')[-1].split('_v')[-1].replace('.json', '')
        self.fda_approved_drugs_path = database_downloads["fda_approved_drugs"]
        self.fda_approved_drugs_version = self.fda_approved_drugs_path.split('/')[-1].split('_v')[-1].replace('.pickle', '')
        self.autocomplete_path = database_downloads["autocomplete"]
        self.autocomplete_version = self.autocomplete_path.split('/')[-1].split('_v')[-1].replace('.sqlite', '')
        self.explainable_dtd_db_path = database_downloads["explainable_dtd_db"]
        self.explainable_dtd_db_version = self.explainable_dtd_db_path.split('/')[-1].split('_v')[-1].replace('.db', '')

        # Set up mysql feedback
        self.mysql_feedback_host = self.config_secrets["mysql_feedback"]["host"]
        self.mysql_feedback_port = self.config_secrets["mysql_feedback"]["port"]
        self.mysql_feedback_username = self.config_secrets["mysql_feedback"]["username"]
        self.mysql_feedback_password = self.config_secrets["mysql_feedback"]["password"]

        # Set up correct Plover URL (since it's not registered in SmartAPI)
        plover_url_override_value = self._read_override_file(f"{file_dir}/plover_url_override.txt")
        if plover_url_override_value:
            self.plover_url = plover_url_override_value
        elif self.maturity in {"production", "prod"}:
            self.plover_url = self.config_dbs["plover"]["prod"]
        elif self.maturity in {"testing", "test"}:
            self.plover_url = self.config_dbs["plover"]["test"]
        else:  # Includes staging, development
            self.plover_url = self.config_dbs["plover"]["dev"]

        # TEMPORARILY set KG2 url here until pulled from SmartAPI; TODO: remove this when #1466 is done
        kg2_url_override_value = self._read_override_file(f"{file_dir}/kg2_url_override.txt")
        if kg2_url_override_value:
            self.rtx_kg2_url = kg2_url_override_value
        elif self.is_itrb_instance:
            if self.maturity in {"production", "prod"}:
                self.rtx_kg2_url = "https://kg2.transltr.io/api/rtxkg2/v1.2"
            elif self.maturity in {"testing", "test"}:
                self.rtx_kg2_url = "https://kg2.test.transltr.io/api/rtxkg2/v1.2"
            else:
                self.rtx_kg2_url = "https://kg2.ci.transltr.io/api/rtxkg2/v1.2"
        else:
            if "NewFmt" in self.instance_name or self.current_branch_name == "NewFmt":
                self.rtx_kg2_url = "https://arax.ncats.io/api/rtxkg2/v1.3"
            elif self.maturity in {"production", "prod"}:
                self.rtx_kg2_url = "https://arax.ncats.io/api/rtxkg2/v1.2"
            else:
                self.rtx_kg2_url = "https://arax.ncats.io/beta/api/rtxkg2/v1.2"
        # TODO: add special exception for CICD (needs to point to localhost KG2)

        # Default to KG2c neo4j
        self.neo4j_kg2 = "KG2c"

        print(f"RTXConfig: Maturity is {self.maturity}, current branch is {self.current_branch_name}, is_itrb_instance="
              f"{self.is_itrb_instance}, plover URL is {self.plover_url}, KG2 URL is {self.rtx_kg2_url}")

    @staticmethod
    def _read_override_file(file_path: str) -> Optional[str]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as override_file:
                lines = override_file.readlines()
                if not lines or not lines[0]:
                    raise ValueError(f"{file_path} exists but does not contain anything! "
                                     f"It should be a single-line file containing the override value.")
                else:
                    return lines[0].strip()
        else:
            return None

    # ### Define attribute version
    @property
    def version(self) -> str:
        return self._version

    @version.setter
    def version(self, version: str):
        self._version = version

    @property
    def neo4j_kg2(self) -> str:
        return self._neo4j_kg2

    @neo4j_kg2.setter
    def neo4j_kg2(self, neo4j_kg2: str):
        self._neo4j_kg2 = neo4j_kg2

        if self.neo4j_kg2 not in self.config_dbs["neo4j"].keys():
            self.neo4j_bolt = None
            self.neo4j_database = None
            self.neo4j_username = None
            self.neo4j_password = None
        else:
            neo4j_instance = self.config_dbs["neo4j"][self.neo4j_kg2]
            self.neo4j_bolt = f"bolt://{neo4j_instance}:7687"
            self.neo4j_database = f"{neo4j_instance}:7474/db/data"
            self.neo4j_username = self.config_secrets["neo4j"][self.neo4j_kg2]["username"]
            self.neo4j_password = self.config_secrets["neo4j"][self.neo4j_kg2]["password"]

    @property
    def neo4j_bolt(self) -> str:
        return self._neo4j_bolt

    @neo4j_bolt.setter
    def neo4j_bolt(self, bolt: str):
        self._neo4j_bolt = bolt

    @property
    def neo4j_database(self) -> str:
        return self._neo4j_database

    @neo4j_database.setter
    def neo4j_database(self, database: str):
        self._neo4j_database = database

    @property
    def neo4j_username(self) -> str:
        return self._neo4j_username

    @neo4j_username.setter
    def neo4j_username(self, username: str):
        self._neo4j_username = username

    @property
    def neo4j_password(self) -> str:
        return self._neo4j_password

    @neo4j_password.setter
    def neo4j_password(self, password: str):
        self._neo4j_password = password

    @property
    def plover_url(self) -> str:
        return self._plover_url

    @plover_url.setter
    def plover_url(self, url: str):
        self._plover_url = url

    @property
    def mysql_feedback_host(self) -> str:
        return self._mysql_feedback_host

    @mysql_feedback_host.setter
    def mysql_feedback_host(self, host: str):
        self._mysql_feedback_host = host

    @property
    def mysql_feedback_port(self) -> str:
        return self._mysql_feedback_port

    @mysql_feedback_port.setter
    def mysql_feedback_port(self, port: str):
        self._mysql_feedback_port = port

    @property
    def mysql_feedback_username(self) -> str:
        return self._mysql_feedback_username

    @mysql_feedback_username.setter
    def mysql_feedback_username(self, username: str):
        self._mysql_feedback_username = username

    @property
    def mysql_feedback_password(self) -> str:
        return self._mysql_feedback_password

    @mysql_feedback_password.setter
    def mysql_feedback_password(self, password: str):
        self._mysql_feedback_password = password


def main():
    rtxConfig = RTXConfiguration()
    print("RTX Version string: " + rtxConfig.version)
    print("neo4j KG2 version: %s" % rtxConfig.neo4j_kg2)
    print("neo4j bolt: %s" % rtxConfig.neo4j_bolt)
    print("neo4j database: %s" % rtxConfig.neo4j_database)
    print("neo4j username: %s" % rtxConfig.neo4j_username)
    print("neo4j password: %s" % rtxConfig.neo4j_password)
    print("plover url: %s" % rtxConfig.plover_url)
    print("rtx-kg2 url: %s" % rtxConfig.rtx_kg2_url)
    print("mysql feedback host: %s" % rtxConfig.mysql_feedback_host)
    print("mysql feedback port: %s" % rtxConfig.mysql_feedback_port)
    print("mysql feedback username: %s" % rtxConfig.mysql_feedback_username)
    print("mysql feedback password: %s" % rtxConfig.mysql_feedback_password)
    print(f"maturity: {rtxConfig.maturity}")
    print(f"current branch: {rtxConfig.current_branch_name}")
    print(f"is_itrb_instance: {rtxConfig.is_itrb_instance}")


if __name__ == "__main__":
    main()
