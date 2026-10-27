"""
This module implements the Galene administrative API client.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging

import requests
from requests.auth import HTTPBasicAuth


# Galene requires an absolute expiry time in RFC 3339 format.
EXPIRES_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class GaleneError(Exception):
    """Base class for Galene client errors."""


class GaleneUnavailable(GaleneError):
    """Galene cannot be reached or answered unexpectedly.

    Callers treat this as "video is not available right now" and never let it
    break gameplay.
    """


class GaleneConflict(GaleneError):
    """A precondition failed: the object exists or changed concurrently."""


class GaleneClient:
    """Minimal client for the Galene administrative API.

    The API lives under /galene-api/v0/ and requires an administrator account
    with the "admin" permission. Groups are created with an "If-None-Match: *"
    precondition, and every mutation that targets an existing object carries
    the entity tag read beforehand so a concurrent change is never lost.
    """

    def __init__(self, config, session=None):
        self.config = config
        self.session = session or requests.Session()
        self.session.auth = HTTPBasicAuth(config.admin_user, config.admin_password)

    # -- low level helpers ---------------------------------------------------

    def _request(self, method, path, *, body=None, headers=None, expect=()):
        url = self.config.api_base + path
        try:
            response = self.session.request(
                method, url,
                json=body,
                headers=headers or {},
                timeout=self.config.timeout,
                verify=self.config.verify_tls,
            )
        except requests.RequestException as exception:
            raise GaleneUnavailable(
                "%s %s failed: %s" % (method, path, exception)) from exception

        if response.status_code in expect:
            return response
        if response.status_code in (412, 409):
            raise GaleneConflict(
                "%s %s returned %s" % (method, path, response.status_code))
        raise GaleneUnavailable(
            "%s %s returned %s: %s" % (
                method, path, response.status_code, response.text[:200]))

    @staticmethod
    def _etag(response):
        return (response.headers.get("ETag") or "").strip()

    def _group_path(self, group):
        return "/.groups/%s/" % group

    # -- groups --------------------------------------------------------------

    def create_group(self, group, *, display_name=None, description=None,
                     max_clients=None, expires=None):
        """Create a group. Raises GaleneConflict when it already exists."""
        body = {}
        if display_name:
            body["displayName"] = display_name
        if description:
            body["description"] = description
        if max_clients:
            body["max-clients"] = int(max_clients)
        if expires:
            body["expires"] = expires.strftime(EXPIRES_FORMAT)

        self._request(
            "PUT", self._group_path(group),
            body=body,
            headers={"If-None-Match": "*"},
            expect=(201,))

    def list_groups(self):
        """Return the names of all groups defined on the server."""
        response = self._request("GET", "/.groups/", expect=(200,))
        try:
            names = response.json()
        except ValueError as exception:
            raise GaleneUnavailable("invalid group list: %s" % exception)
        if names is None:
            # An empty group list is serialised as null.
            return []
        if not isinstance(names, list):
            raise GaleneUnavailable("invalid group list")
        return [name for name in names if isinstance(name, str)]

    def get_group_etag(self, group):
        response = self._request("HEAD", self._group_path(group), expect=(200,))
        return self._etag(response)

    def delete_group(self, group, etag):
        """Delete a group. The etag can be empty when reading it failed."""
        headers = {"If-Match": etag} if etag else {}
        self._request(
            "DELETE", self._group_path(group),
            headers=headers, expect=(204, 404))

    # -- tokens --------------------------------------------------------------

    def _token_path(self, group, token):
        return "%s.tokens/%s" % (self._group_path(group), token)

    def create_token(self, group, *, username, permissions, expires=None):
        """Create a join token and return its name.

        Galene names generated tokens itself: naming one explicitly through PUT
        hits a nil dereference in the 1.2.x server, so the generated name from
        the Location header is used instead. Only POST is used here.
        """
        body = {
            "username": username,
            "permissions": list(permissions),
        }
        if expires:
            body["expires"] = expires.strftime(EXPIRES_FORMAT)

        response = self._request(
            "POST", "%s.tokens/" % self._group_path(group),
            body=body, expect=(201,))

        token = (response.headers.get("Location") or "").strip()
        if not token:
            raise GaleneUnavailable("Galene returned no token name")
        return token

    def get_token_etag(self, group, token):
        response = self._request(
            "GET", self._token_path(group, token), expect=(200,))
        return self._etag(response)

    def update_token(self, group, token, *, username, permissions, expires=None):
        """Replace the value of an existing token."""
        etag = self.get_token_etag(group, token)
        body = {
            "username": username,
            "permissions": list(permissions),
        }
        if expires:
            body["expires"] = expires.strftime(EXPIRES_FORMAT)
        self._request(
            "PUT", self._token_path(group, token),
            body=body,
            headers={"If-Match": etag},
            expect=(204,))

    def delete_token(self, group, token):
        try:
            etag = self.get_token_etag(group, token)
        except GaleneUnavailable:
            return
        self._request(
            "DELETE", self._token_path(group, token),
            headers={"If-Match": etag},
            expect=(204, 404))

    def list_tokens(self, group):
        response = self._request(
            "GET", "%s.tokens/" % self._group_path(group), expect=(200,))
        try:
            names = response.json()
        except ValueError as exception:
            raise GaleneUnavailable("invalid token list: %s" % exception)
        if names is None:
            return []
        if not isinstance(names, list):
            raise GaleneUnavailable("invalid token list")
        return names
