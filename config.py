import copy
import json


class Config:
	_config: dict[str, any] = None

	_default_config: dict[str, any] = {
		"chrome_location":        r".\chromium\chrome.exe",
		"template_url":           "https://vizzy.io/editor?project=1fr6ZmEqOSqm4XNFlWJ93",
		"vizzy_email":            "<enter email>",
		"vizzy_password":         "<enter password>",
		"autohotkey_location":    r"C:\Program Files\AutoHotkey\AutoHotkeyU64.exe",
		"openfile_ahk_script":    r".\openfile.ahk",
		"savefile_ahk_script":    r".\savefile.ahk",
		"ffmpeg_location":        r".\ffmpeg\bin\ffmpeg.exe",
		"ffprobe_location":       r".\ffmpeg\bin\ffprobe.exe",
		"thread_count":           2,
		"savestate_file":         r".\savestate.json",
		"state":                  "",
		"credentials":            {},
		"next_publish_date":      "2023-01-01T00:00:00",
		"publish_interval_hours": 12,
		"autosave_interval_mins": 10,
		"title_format":           "Nightnightcore - {title} ({artist})",
		"description_format":     "Make sure to like and subscribe for more daily uploads!\n\n\
Nightnightcore Remix of {title} by {artist}\n\
Original Song: {yt_url}\n\n\
A nightnightcore edit is a remix track that speeds up the pitch and time of nightcore by 10-30% giving it \
faster tempos, more energetic feel, and higher-pitched vocals\n\n\
#nightcore"
	}

	_config_location = "./config.json"

	@staticmethod
	def set_config_location (path: str) -> None:
		"""
		Sets the location of the config file, and reloads the config.
		:param path: The path of the config file to read
		:return: None
		"""
		Config._config_location = path
		Config.reload_config()

	@staticmethod
	def reload_config () -> None:
		"""
		Reloads the config file from disk, creating it with the default values if it doesn't exist.
		:return: None
		"""
		try:
			with open(Config._config_location, "r") as config_file:
				Config._config = json.load(config_file)
		except FileNotFoundError:
			with open(Config._config_location, "w") as config_file:
				json.dump(Config._default_config, config_file)
				Config._config = copy.deepcopy(Config._default_config)

	@staticmethod
	def get (name: str) -> any:
		"""
		Gets a config value by name.
		:param name: The config value to get
		:return: The config value set, or None if it's not found
		"""
		if Config._config is None:
			Config.reload_config()

		if name not in Config._config:
			Config.set(name, Config._default_config[name])  # Write the defaults to the config file if uninitialised

		return Config._config[name]

	@staticmethod
	def set (name: str, value: any) -> None:
		"""
		Sets a config value by name.
		:param name: The config value to set.
		:param value: The value to write.
		:return: None
		"""
		if Config._config is None:
			Config.reload_config()
		Config._config[name] = value
		with open(Config._config_location, "w") as config_file:
			json.dump(Config._config, config_file)
