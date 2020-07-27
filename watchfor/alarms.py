import logging
import datetime
from collections import namedtuple

from .exceptions import ConfError
from .results_mgr import ResultsMgr
from .collector_memory import CollectorMemory


__all__ = ["Alarms"]


log = logging.getLogger(__name__)

DangerLevel = namedtuple("DangerLevel", "danger fails raises alarms")

ONE_DAY = datetime.timedelta(days=1)
DAYS_3 = datetime.timedelta(days=3)
DAYS_7 = datetime.timedelta(days=7)


class Alarms:

	def __init__(self, cfg, mta=None):

		self._mta = mta
		self._now = datetime.datetime.now()

		self._config = {}

		# TODO: support for schema versioning

		for k, v in cfg.items():

			if not isinstance(v, dict):
				continue

			danger_levels = []

			for case in v['when']:
				danger_levels.append(DangerLevel(
					int(case.get('danger', 1)),
					int(case.get('fails', 1)),
					int(case.get('raises', 1)),
					case['alarms']
				))

			danger_levels.sort(key=lambda i: -i.danger)

			self._config[k] = danger_levels

		if 'default' not in self._config:
			raise ConfError("_alarms.yml the \"edfault\" section is missing")

	def __call__(self, collector: CollectorMemory, latest_results: ResultsMgr, html_message: [str, bytes]):

		alarms_to_sound = self.update_latest_results(collector, latest_results)
		if collector.has_errors:
			if alarms_to_sound:

				for danger_level in sorted(alarms_to_sound.values(), key=lambda i: -i.danger):

					log.warning(f"Errors found and reporting them with danger level {danger_level.danger}")
					# Only the highest level of alarm is reported
					self.send_alarm(danger_level.alarms, html_message)

					break
			else:
				log.warning("Errors found but seem to be already reported")

			return True
		return False

	def update_latest_results(self, collector: CollectorMemory, latest_results: ResultsMgr):

		# TODO: add support for multiple alarms configurations
		danger_levels = self._config['default']

		alarms_to_sound = {}

		for config in collector.data:

			cfg_path = config['config']

			for site in config['sites']:
				for check in site['checks']:
					if check['type'] == 'check_success':
						entry = latest_results.update_success(cfg_path, check)

						for level in danger_levels:
							if check['danger'] >= level.danger:

								if entry['raises'] >= level.raises:
									latest_results.recovery_issued(cfg_path, check)

									# TODO: send notifications from recovery
									# recoveries[id(level)] = level["alarms"]
								break

					elif check['type'] == 'check_failure':
						entry = latest_results.update_failure(cfg_path, check)

						for level in danger_levels:
							if check['danger'] >= level.danger:

								if entry['fails'] >= level.fails:

									min_period = ONE_DAY
									if entry['first_fail'] + DAYS_3 < self._now:
										min_period = DAYS_7

									if not entry['latest_alarm'] or entry['latest_alarm'] + min_period < self._now:

										latest_results.alarm_issued(cfg_path, check)
										alarms_to_sound[id(level)] = level

								break

		return alarms_to_sound

	def send_alarm(self, alarms, html_message):

		if 'mail' in alarms:
			for mail in alarms['mail']:
				log.warning(f"Sending report email to \"{mail}\"")
				self._mta.send(mail, html_message)

		if 'execute' in alarms:
			for _cmd in alarms['execute']:
				log.warning(f"Sending report to cmd: \"{_cmd}\"")
				# TODO: implement
				# os.system(cmd)
				pass

		if 'slack' in alarms:
			for _slack in alarms['slack']:
				# TODO: implement
				pass

		# TODO: raise an error when other (unimplemented) type of alarm is found
