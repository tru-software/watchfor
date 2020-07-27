import logging


logging.config.dictConfig({
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': {
		'standard': {
			'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
		},
	},
	'handlers': {
		'console': {
			'formatter': 'standard',
			'level': 'INFO',
			'class': 'logging.StreamHandler',
		}
	},
	'loggers': {
		'': {
			'handlers': ['console'],
			'level': 'INFO',
		}
	}
})
