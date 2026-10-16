# -*- coding: utf-8 -*-
# Audio Equalizer para NVDA - Install Tasks
# Copyright (C) 2026 Daliana
# Released under the GNU General Public License version 2 (GPLv2)

import os
from logHandler import log


def onInstall():
	"""Se ejecuta al instalar o actualizar el complemento."""
	log.info("Audio Equalizer: instalación completada.")


def onUninstall():
	"""
	Se ejecuta al desinstalar el complemento desde el administrador de complementos de NVDA.
	Limpia las referencias de configuración de audioEqualizer en nvda.ini si existen.
	"""
	try:
		import config
		conf_obj = getattr(config, "conf", None)
		modified = False
		if conf_obj is not None:
			if "audioEqualizer" in conf_obj:
				try:
					del conf_obj["audioEqualizer"]
					modified = True
				except Exception:
					pass
			try:
				spec = getattr(conf_obj, "spec", {})
			except Exception:
				spec = {}
			try:
				if "audioEqualizer" in spec:
					del conf_obj.spec["audioEqualizer"]
					modified = True
			except Exception:
				pass
			if modified and hasattr(conf_obj, "save"):
				try:
					conf_obj.save()
				except Exception:
					pass
		log.info("Audio Equalizer: configuración eliminada del perfil al desinstalar.")
	except Exception as e:
		log.warning(f"Audio Equalizer: error al limpiar configuración en desinstalación: {e}")
	try:
		import globalVars
		config_path = getattr(getattr(globalVars, "appArgs", None), "configPath", None)
		if config_path:
			for log_name in (
				"audioEqualizer.log",
				"audioEqualizer.log.old",
				"audioEqualizer_user_profiles.json",
				"audioEqualizer_user_profiles.json.tmp",
				"audioEqualizer_factory_overrides.json",
				"audioEqualizer_factory_overrides.json.tmp",
				"audioEqualizer_state.json",
				"audioEqualizer_state.json.tmp",
			):
				log_p = os.path.join(config_path, log_name)
				if os.path.exists(log_p):
					try: os.remove(log_p)
					except OSError: pass
	except Exception:
		pass
	try:
		apo_dirs = [
			os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "EqualizerAPO"),
			os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), "EqualizerAPO"),
			r"C:\Program Files\EqualizerAPO"
		]
		for apo_dir in apo_dirs:
			config_dir = os.path.join(apo_dir, "config")
			main_config = os.path.join(config_dir, "config.txt")
			addon_config = os.path.join(config_dir, "nvda_equalizer.txt")
			if os.path.exists(addon_config):
				try: os.remove(addon_config)
				except OSError: pass
			if os.path.exists(main_config):
				tmp_path = main_config + ".tmp"
				try:
					try:
						if os.path.getsize(main_config) > 1024 * 1024:
							log.warning("Audio Equalizer: config.txt supera 1 MB; se omite limpieza por seguridad.")
							continue
					except OSError:
						pass
					with open(main_config, "r", encoding="utf-8-sig") as f:
						content = f.read(1024 * 1024 + 1)
					if len(content) > 1024 * 1024:
						log.warning("Audio Equalizer: config.txt supera 1 MB; se omite limpieza por seguridad.")
						continue
					lines = content.splitlines(keepends=True)
					new_lines = [l for l in lines if "nvda_equalizer.txt" not in l]
					if len(new_lines) != len(lines):
						with open(tmp_path, "w", encoding="utf-8") as f:
							f.writelines(new_lines)
						for _attempt in range(3):
							try:
								os.replace(tmp_path, main_config)
								break
							except OSError:
								if _attempt == 2:
									raise
								try:
									import time as _time_mod
									_time_mod.sleep(0.1 * (_attempt + 1))
								except Exception:
									pass
				except Exception:
					pass
				finally:
					try:
						if os.path.exists(tmp_path):
							os.remove(tmp_path)
					except OSError:
						pass
	except Exception:
		pass
