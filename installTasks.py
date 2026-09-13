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
		modified = False
		if "audioEqualizer" in config.conf:
			del config.conf["audioEqualizer"]
			modified = True
		if "audioEqualizer" in getattr(config.conf, "spec", {}):
			del config.conf.spec["audioEqualizer"]
			modified = True
		if modified:
			config.conf.save()
		log.info("Audio Equalizer: configuración eliminada del perfil al desinstalar.")
	except Exception as e:
		log.warning(f"Audio Equalizer: error al limpiar configuración en desinstalación: {e}")
	try:
		import globalVars
		for log_name in ("audioEqualizer.log", "audioEqualizer.log.old"):
			log_p = os.path.join(globalVars.appArgs.configPath, log_name)
			if os.path.exists(log_p):
				try: os.remove(log_p)
				except OSError: pass
	except Exception:
		pass
