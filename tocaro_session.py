#!/usr/bin/env python3

import re
import json
from logging import getLogger
from time import time, sleep

from requests import session, Response
from bs4 import BeautifulSoup

class CsrfTokenNotFoundError(Exception):
  pass

class AuthTokenNotFoundError(Exception):
  pass

class SignInError(Exception):
  pass

class TocaroSession():

  logger = getLogger(__name__)

  __base_url = "https://tocaro.im"
  __signin_url = __base_url + "/sign-in"
  __groups_url = __base_url + "/api/v3/groups"
  __messages_url = __groups_url + "/%s/messages"

  signin_data = {
    "email": "",
    "password": "",
    "sso_failback": "",
    "commit": "サインイン",
    "authenticity_token": ""
  }

  def __init__(self):
    self.session = session()
    self.now = int(time() * 100)

  def get_csrf_token(self, html: str) -> str:
    soup = BeautifulSoup(html,"html.parser")
    form_input_dom = soup.select(".submitOnce input")
    for i in form_input_dom:
      if i.attrs["name"] == "authenticity_token":
        return i.attrs["value"]
    raise CsrfTokenNotFoundError("csrf token(authenticity_token) not found.")

  def signin(self, email: str, password: str) -> Response:
    self.signin_data["email"] = email
    self.signin_data["password"] = password

    res = self.session.get(self.__signin_url)
    csrf_token = self.get_csrf_token(res.text)
    self.logger.info("got csrf token: " + csrf_token)
    self.signin_data["authenticity_token"] = csrf_token

    res = self.session.post(self.__signin_url, data=self.signin_data)
    if "メールアドレスかパスワードが間違っています。" in res.text:
      raise SignInError("signin failed. needs confirm username or password.")
    res.raise_for_status()
    self.logger.info("signin successfully.")

    self.auth_token = self.get_auth_token(res)
    return res

  def get_auth_token(self, html: Response) -> str:
    for line in html.iter_lines():
      self.logger.debug("processing html line: " + line.decode(encoding="utf-8"))
      result = re.findall("var\sbootData\s=\s(.*)", line.decode(encoding="utf-8"))
      if len(result) > 0:
        json_data = json.loads(result[0])
        self.logger.debug("got your tocaro bootData: " + str(json_data))
        return json_data["currentUser"]["credentials"]["tocaro"]["token"]

  def get_groups(self, group_type: str = "show") -> dict:
    if not self.auth_token:
      raise AuthTokenNotFoundError()

    self.logger.debug("using auth_token: " + self.auth_token)
    self.logger.info("let's get your joined groups.")
    res = self.session.get(
        self.__groups_url, 
        headers={"authorization": "Bearer " + self.auth_token},
        params={"type": group_type, "t": self.now}
    )
    res.raise_for_status()
    self.logger.info("got group successfully.")
    return res.json()

  def get_messages(self, group_id: str, next_id: str = "") -> dict:
    if not self.auth_token:
      raise AuthTokenNotFoundError()

    self.logger.debug("using auth_token: " + self.auth_token)
    self.logger.info("let's get messages. target group is " + group_id)

    params = {"t": self.now}
    if next_id:
      params["ulid"] = next_id

    res = self.session.get(
        self.__messages_url % group_id, 
        headers={"authorization": "Bearer " + self.auth_token},
        params=params
    )
    res.raise_for_status()
    self.logger.info("got message successfully.")
    return res.json()

  def get_all_messages(self, group_id: str, interval: float = 0.3) -> dict:
    self.logger.info("let's get all messages. target group is " + group_id)

    messages = []
    next_id = ""
    while True:
      new = self.get_messages(group_id, next_id=next_id)
      if not new:
        break
      messages.extend(new)
      next_id = messages[-1]["ulid"]
      self.logger.debug("next message id: " + next_id)
      sleep(interval)

    self.logger.info("got all message successfully.")
    return messages
