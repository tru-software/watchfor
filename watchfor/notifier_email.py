import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import email.charset as Charset
from email.header import Header

from smtplib import SMTP, SMTP_SSL, SMTPNotSupportedError

from .notifier_base import NotifierBase


DEFAULT_CHARSET = 'utf-8'
Charset.add_charset(DEFAULT_CHARSET, Charset.SHORTEST, Charset.BASE64, DEFAULT_CHARSET)


def _force_ascii(s):
	try:
		s.encode('ascii')
		return s
	except UnicodeEncodeError:
		return Header(s, 'utf-8').encode()


class EMailNotifier(NotifierBase):

	def __init__(self, cfg):
		super().__init__()

		self._server = cfg["host"]
		self._port = int(cfg.get("port", 587))
		self._user = cfg.get("user", '')
		self._password = cfg.get("password", '')
		self._ssl = cfg["ssl"]
		self._tls = cfg["tls"]
		self._from = cfg["from"]

		self._receivers = cfg["receivers"]

	def send(self, content, receivers=None):

		for receiver in receivers or self._receivers:

			from_ = self._from

			email = self.componse_email(
				subject="WatchFor ALERT!",
				from_=from_,
				to=receiver,
				html_content=content
			)
			SMTP_cls = SMTP_SSL if self._ssl else SMTP

			with SMTP_cls(self._server, self._port) as smtp:
				smtp.ehlo()
				if self._tls and not self._ssl:
					smtp.starttls()
					smtp.ehlo()

				if self._user and self._password:
					smtp.login(self._user, self._password)

				content = email.as_string()

				if smtp.has_extn('smtputf8'):
					smtp.sendmail(from_, receiver, content, mail_options=["smtputf8"])
				else:
					smtp.sendmail(_force_ascii(from_), _force_ascii(receiver), content)

				smtp.quit()

	def componse_email(self, subject, from_, to, html_content, reply_to=None, text_content=None):

		msgRoot = MIMEMultipart('related')
		msgRoot['Subject'] = Header(subject, 'utf-8')
		msgRoot['From'] = from_
		msgRoot['To'] = to
		msgRoot['Date'] = email.utils.formatdate()
		if reply_to:
			msgRoot['Reply-To'] = reply_to
			msgRoot['Mail-Reply-To'] = reply_to
			msgRoot['Mail-Followup-To'] = reply_to
		msgRoot.preamble = 'This is a multi-part message in MIME format.'

		msgAlternative = MIMEMultipart('alternative')
		msgRoot.attach(msgAlternative)

		if text_content:
			msgAlternative.attach(MIMEText(text_content.encode(DEFAULT_CHARSET), 'plain', _charset=DEFAULT_CHARSET))

		if html_content:
			msgAlternative.attach(MIMEText(html_content.encode(DEFAULT_CHARSET), 'html', _charset=DEFAULT_CHARSET))

		return msgRoot
