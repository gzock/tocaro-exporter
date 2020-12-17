#!/usr/bin/env python3

import os
from configparser import ConfigParser
from time import sleep
from logging import getLogger, basicConfig, INFO, DEBUG
import json
from distutils.util import strtobool

from tocaro_session import TocaroSession

CONFIG_INI = "./config.ini"

def save_json(content, output_path):
  with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(content, f, indent=4, ensure_ascii=False)

def main():
  logger = getLogger(__name__)

  logger.info("tocaro exporter execution start.")
  logger.info("reading config...")
  config = ConfigParser()
  if not os.path.exists(CONFIG_INI):
    logger.error("config.ini not exists.")
    exit(1)
  config.read(CONFIG_INI, encoding='utf-8')

  if strtobool(config["common"]["debug"]):
    getLogger().setLevel(DEBUG)
    logger.debug("enable debug logging.")

  logger.info("connect to tocaro.")
  tocaro = TocaroSession()
  tocaro.signin(
      email=config["account"]["email"], 
      password=config["account"]["password"]
  )

  group_type = config["common"]["group_type"]
  if group_type not in ["show", "hide"]:
    logger.error("group_type invalid. valid value: show, hide")
    raise Exception

  groups = tocaro.get_groups(group_type)
  if strtobool(config["output"]["with_groups"]):
    output_path = "%s/groups.json" % config["output"]["path"]
    save_json(groups, output_path)

  for group in groups:
    if group["type"] not in ["group", "talk"]:
      logger.debug("group_id: %s, group type isn't group or talk. processing will be skip." % group["code"])
      continue

    if config["common"]["excludes"] in group["name"]:
      logger.debug("group_id: %s, contain excudes string in group name. processing will be skip." % group["code"])
      continue

    logger.info("get message from group_id: " + group["code"])
    messages = tocaro.get_all_messages(group_id=group["code"])

    output_path = "%s/%s.json" % (config["output"]["path"], group["code"])
    logger.info("message saving... output path: " + output_path)

    save_json(messages, output_path)

    sleep(int(config["common"]["interval"]))

if __name__ == "__main__":
  basicConfig(
      format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S'
  )

  getLogger().setLevel(INFO)
  main()
