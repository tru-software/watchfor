<html>
<%page expression_filter="h"/>
<%!
%>
<%def name="Title()">Alert</%def>
<head>
	<title>${self.Title()}</title>

	<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
	<meta http-equiv="Content-Language" content="pl" />
	<meta http-equiv="X-UA-Compatible" content="IE=edge" />

	<style type="text/css">
	</style>
</head>
<body>
	<table border="0" cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;margin: 0; padding: 0; width:100%;" width="100%">
		<tbody>
			<tr>
				<td align="center" bgcolor="#e3e3e3" style="font-family:Arial,sans-serif;width:100%;" valign="top" width="100%">
					% for cfg in data:
						% for error in cfg['errors']:
							ERROR FOUND in <code>${site['config']}</code><br/>
							<p>${error['error']}</p>
						% endfor
						% for site in cfg['sites']:
							<table border="0" cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;margin: 20px; padding: 0; max-width:900px;" width="900">
								<tbody>
										<tr>
											<td align="center" bgcolor="#ffffff" style="font-family:Arial,sans-serif;width:900px;border-radius:15px;-webkit-border-radius:15px;-moz-border-radius:15px;-ms-border-radius:15px;padding:20px;margin:20px auto;" valign="top" width="900">
												${Site(cfg['config'], site)}
											</td>
										</tr>
								</tbody>
							</table>
						% endfor
					% endfor
				</td>
			</tr>
		</tbody>
	</table>
</body>


<%def name="DateTime(dt)">
	<span class="dt">${dt.strftime("%Y.%m.%d %H:%M:%S")}</span>
</%def>


<%def name="Site(cfg_path, site)">
	<table border="0" cellpadding="0" cellspacing="0" style="font-family:Arial,sans-serif;margin: 0; padding: 0; max-width:900px;width:100%;" width="100%">
		<tbody>
			<tr>
				<td style="font-family:Arial,sans-serif;width:65%;" width="65%">
					<b>ALERT FOR SITE: <a href="${site['url']}">${site['url']}</a></b><br/>
					<span style="color:#6d6d6d;font-size:10px;">Config file: <code>${cfg_path}</code></span>
				</td>
				<td align="right" style="width:35%;font-family:Arial,sans-serif;color:#6d6d6d;font-size:10px;" width="35%">
					<span style="width:35%;font-family:Arial,sans-serif;color:#6d6d6d;font-size:10px;">
						${DateTime(site['time'])}<br/>
						host: <b>${hostname|h}</b>
					</span>
				</td>
			</tr>
			<tr>
				<td colspan="2" style="font-family:Arial,sans-serif;width:100%;color:#4d4d4d;padding:20px 0 0 0" width="100%">
				</td>
			</tr>
			% for error in site['errors']:
				<tr>
					<td colspan="2" style="font-family:monospace,sans-serif;width:100%;color:#4d4d4d;padding:20px 0 0 0" width="100%">
						ERROR: ${error['error']}
					</td>
				</tr>
			% endfor
			% for check in site['checks']:
				<tr>
					<td colspan="2" style="font-family:monospace,sans-serif; font-size:11px; width:100%;color:#4d4d4d;" width="100%">
						<code>${DateTime(check['time'])}</code>
						% if check['type'] == 'start_check':
							% if check['cfg'].get('title'):
								<b>${check['cfg']['title']}</b>
							% else:
								<i>Unamed check</i>
							% endif
						% elif check['type'] == 'check_error':
							## TODO:
							<code>${check}</code>
						% elif check['type'] == 'open_url':
							<code><b>${check['method']}</b></code>
							<code>${check['url']}</code>
						% elif check['type'] == 'open_url_timeout':
							## TODO:
							<code>${check}</code>
						% elif check['type'] == 'open_url_response':
							Response: <b>HTTP${check['response'].status}</b>
							[<span style="color:#4d4dfd;">${int(check['diff']*1000)}ms</span>]
						% elif check['type'] == 'check_success':
							## TODO:
							<code>${check}</code>
						% elif check['type'] == 'check_failure':
							## TODO:
							<b>${check['check']}</b>
							${check['error']}
						% endif
					</td>
				</tr>
			% endfor
			<tr>
				<td colspan="2" style="font-family:Arial,sans-serif;width:100%;color:#6d6d6d;padding:20px 0 0 0;font-size: 10px;" width="100%">
					${self.OrderDisclaimer()}
					${self.Footer()}
				</td>
			</tr>
		</tbody>
	</table>
</%def>

<%def name="OrderDisclaimer()">
</%def>

<%def name="Footer()">
	<small>This is an alert sent by a monitor application.<br/>
	For details visit <a href="https://github.com/tru-software/watchfor">https://github.com/tru-software/watchfor</a></small>
</%def>


