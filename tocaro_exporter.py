#!/usr/bin/env python3

import os
from argparse import ArgumentParser
from configparser import ConfigParser
from logging import getLogger, basicConfig, INFO, DEBUG
import json
from distutils.util import strtobool

from tocaro_session import TocaroSession, CsrfTokenNotFoundError, SignInError

class TocaroExporter():
  logger = getLogger(__name__)
  group_type = "show"
  interval = 0.3

  def __init__(self, email="", password=""):
    self.tocaro = TocaroSession()
    if email and password:
      self.signin(email, password)

  def signin(self, email, password):
    self.tocaro.signin(email, password)

  def get_groups(self):
    if self.group_type not in ["show", "hide"]:
      self.logger.error("group_type invalid. valid value: show, hide")
      raise Exception

    return self.tocaro.get_groups(self.group_type)

  def export_groups(self, output_path):
    groups = self.get_groups()

    __path = "%s/groups.json" % output_path
    self.logger.info("groups saving... output path: " + __path)
    self.__save_json(groups, __path)

  def gather_group_ids(self, groups, includes="", excludes=""):
    ret = []
    for group in groups:
      if group["type"] not in ["group", "talk"]:
        self.logger.debug("group_id: %s, group type isn't group or talk. processing will be skip." % group["code"])
        continue

      if excludes and excludes in group["name"]:
        self.logger.debug("group_id: %s, contain excudes string in group name. processing will be skip." % group["code"])
        continue

      if includes and includes not in group["name"]:
        self.logger.debug("group_id: %s, not include string in group name. processing will be skip." % group["code"])
        continue

      ret.append(group["code"])
    return ret
    
  def export_messages(self, output_path, group_id="", includes="", excludes=""):
    group_ids = []

    if group_id:
      group_ids.append(group_id)

    else:
      groups = self.get_groups()
      group_ids.extend(
          self.gather_group_ids(groups, includes, excludes)
      )

    self.logger.info("gatherd group id list: " + str(group_ids))

    for group_id in group_ids:
      self.logger.info("get message from group_id: " + group_id)
      messages = self.tocaro.get_all_messages(
          group_id=group_id,
          interval=float(self.interval)
      )
      __path = "%s/%s.json" % (output_path, group_id)
      self.logger.info("messages saving... output path: " + __path)
      self.__save_json(messages, __path)

  def __save_json(self, content, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
      json.dump(content, f, indent=4, ensure_ascii=False)


def InvalidArgsError(Exception):
  pass
  
def main(args):
  logger = getLogger(__name__)
  logger.info("tocaro exporter execution start.")

  if 2 > sum(list(map(lambda x: bool(vars(args)[x]), vars(args)))):
    logger.error("specified arguments is wrong.")
    exit(1)

  logger.info("reading config...")
  config = ConfigParser()
  if not os.path.exists(args.config):
    logger.error("specified config file not exists.")
    exit(1)
  config.read(args.config, encoding='utf-8')

  if strtobool(config["common"]["debug"]):
    getLogger().setLevel(DEBUG)
    logger.debug("enable debug logging.")

  logger.info("connect to tocaro.")
  try:
    exporter = TocaroExporter(
        email=config["account"]["email"], 
        password=config["account"]["password"]
    )
  except (CsrfTokenNotFoundError, SignInError) as e:
    logger.error("signin processing unsuccessfully... please, check error message: " + str(e))
    exit(1)

  exporter.group_type = config["common"]["group_type"]
  exporter.interval = config["common"]["interval"]

  if args.group_only:
    exporter.export_groups(config["output"]["path"])

  else:
    exporter.export_messages(
        output_path=config["output"]["path"],
        group_id=args.group_id,
        includes=args.includes,
        excludes=config["common"]["excludes"]
    )
  logger.info("processing sucessfully.")


if __name__ == "__main__":
  basicConfig(
      format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S'
  )

  getLogger().setLevel(INFO)

  parser = ArgumentParser(description="Tocaro Exporter")
  parser.add_argument("-c", "--config", default="./config.ini", help="specify config file path.")
  parser.add_argument("-a", "--all", action="store_true", help="export all messages from all groups.")
  parser.add_argument("-g", "--group-id", help="export messages from specified group.")
  parser.add_argument("-i", "--includes", help="export message from groups including the specified string.")
  parser.add_argument("--group-only", action="store_true", help="export for group list json only.")
  args = parser.parse_args()  

  main(args)
