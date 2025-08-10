import logging
import time

import requests

from synapse.module_api import JsonDict, ModuleApi
from synapse.types import UserID

logger = logging.getLogger(__name__)


class RestAuthProvider:
	def __init__(self, config, account_handler: ModuleApi):
		self.api = account_handler

		if not config.endpoint:
			raise RuntimeError("Missing endpoint config")

		self.endpoint = config.endpoint
		self.regLower = config.regLower
		self.config = config

		logger.info("Endpoint: %s", self.endpoint)
		logger.info("Enforce lowercase username during registration: %s", self.regLower)

		self.api.register_password_auth_provider_callbacks(
			check_3pid_auth=self.check_email,
			auth_checkers={("m.login.password", ("password",)): self.check_password},
		)

	async def check_password(
		self, username: str, login_type: str, login_object: JsonDict
	):
		if not login_type == "m.login.password":
			return None

		logger.info("Got password check for " + username)
		data = {"user": {"id": username, "password": login_object.get("password")}}

		return await self.check_auth(data)

	async def check_email(
		self,
		medium: str,
		address: str,
		password: str,
	):
		if not medium == "email":
			return None

		logger.info("Got password check for " + address)
		data = {"user": {"email": address, "password": password}}

		return await self.check_auth(data)

	async def check_auth(self, data):
		r = requests.post(
			self.endpoint + "/_matrix-internal/identity/v1/check_credentials/",
			json=data,
		)
		if r.status_code == 401:  # Unauthorized
			return None
		r.raise_for_status()
		r = r.json()
		if not r["auth"]:
			reason = "Invalid JSON data returned from REST endpoint"
			logger.warning(reason)
			raise RuntimeError(reason)

		auth = r["auth"]

		if not auth["success"]:
			logger.info("User not authenticated")
			return None

		username = auth.get("mxid")

		localpart = username.split(":", 1)[0][1:]
		domain = username.split(":", 1)[1]
		logger.info("User %s authenticated", username)

		display_name = None
		if "profile" in auth:
			display_name = auth["profile"].get("display_name")

		registration = False
		if not (await self.api.check_user_exists(username)):
			logger.info("User %s does not exist yet, creating...", username)

			if localpart != localpart.lower() and self.regLower:
				logger.info(
					"User %s was cannot be created due to username lowercase policy",
					localpart,
				)
				return None

			username = await self.api.register_user(
				localpart=localpart,
				displayname=display_name if self.config.setNameOnRegister else None
			)
			registration = True
			logger.info(
				"Registration based on REST data was successful for %s", username
			)
		else:
			logger.info("User %s already exists, registration skipped", username)

		if auth["profile"]:
			logger.info("Handling profile data")
			profile = auth["profile"]

			store = self.api._hs.get_profile_handler().store

			if "display_name" in profile and self.config.setNameOnLogin:
				logger.info(
					"Setting display name to '%s' based on profile data", display_name
				)
				await store.set_profile_displayname(
					UserID(localpart, domain), display_name
				)
			else:
				logger.info(
					"Display name was not set because it was not given or policy restricted it"
				)

			if self.config.updateThreepid:
				if "three_pids" in profile:
					logger.info("Handling 3PIDs")

					external_3pids = []
					for threepid in profile["three_pids"]:
						medium = threepid["medium"].lower()
						address = threepid["address"].lower()
						external_3pids.append({"medium": medium, "address": address})
						logger.info(
							"Looking for 3PID %s:%s in user profile", medium, address
						)

						validated_at = time_msec()
						if not (await store.get_user_id_by_threepid(medium, address)):
							logger.info("3PID is not present, adding")
							await store.user_add_threepid(
								username, medium, address, validated_at, validated_at
							)
						else:
							logger.info("3PID is present, skipping")

					if self.config.replaceThreepid:
						for threepid in await store.user_get_threepids(username):
							medium = threepid.medium.lower()
							address = threepid.address.lower()
							if {
								"medium": medium,
								"address": address,
							} not in external_3pids:
								logger.info(
									"3PID is not present in external datastore, deleting"
								)
								await store.user_delete_threepid(
									username, medium, address
								)

			else:
				logger.info("3PIDs were not updated due to policy")
		else:
			logger.info("No profile data")

		return (self.api.get_qualified_user_id(username), None)

	@staticmethod
	def parse_config(config):
		# verify config sanity
		_require_keys(config, ["endpoint"])

		class _RestConfig(object):
			endpoint = ""
			regLower = True
			setNameOnRegister = True
			setNameOnLogin = False
			updateThreepid = True
			replaceThreepid = False

		rest_config = _RestConfig()
		rest_config.endpoint = config["endpoint"]

		try:
			rest_config.regLower = config["policy"]["registration"]["username"][
				"enforceLowercase"
			]
		except TypeError:
			# we don't care
			pass
		except KeyError:
			# we don't care
			pass

		try:
			rest_config.setNameOnRegister = config["policy"]["registration"]["profile"][
				"name"
			]
		except TypeError:
			# we don't care
			pass
		except KeyError:
			# we don't care
			pass

		try:
			rest_config.setNameOnLogin = config["policy"]["login"]["profile"]["name"]
		except TypeError:
			# we don't care
			pass
		except KeyError:
			# we don't care
			pass

		try:
			rest_config.updateThreepid = config["policy"]["all"]["threepid"]["update"]
		except TypeError:
			# we don't care
			pass
		except KeyError:
			# we don't care
			pass

		try:
			rest_config.replaceThreepid = config["policy"]["all"]["threepid"]["replace"]
		except TypeError:
			# we don't care
			pass
		except KeyError:
			# we don't care
			pass

		return rest_config

	async def is_3pid_allowed(
		self, medium: str, address: str, registration: bool
	) -> bool:
		return True


def _require_keys(config, required):
	missing = [key for key in required if key not in config]
	if missing:
		raise Exception(
			"REST Auth enabled but missing required config values: {}".format(
				", ".join(missing)
			)
		)


def time_msec():
	"""Get the current timestamp in milliseconds"""
	return int(time.time() * 1000)
