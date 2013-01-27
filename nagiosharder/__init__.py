from urllib import urlencode
from datetime import datetime, timedelta
import requests
import re

from parse import parse_status_html

__all__ = ['Nagios']
__version__ = '0.1.1'

class Nagios:
    def __init__(self, user, password, nagios_url, version):
        self.user = user
        self.password = password
        self.nagios_url = re.sub('r/\/$/', '', nagios_url)
        self.version = version
        # TODO: check time format
        self.nagios_time_format = '%d-%m-%Y %H:%M:%S'

    @property
    def status_url(self):
        return self.nagios_url + '/status.cgi'

    @property
    def cmd_url(self):
        return self.nagios_url + '/cmd.cgi'

    @property
    def extinfo_url(self):
        return self.nagios_url + '/extinfo.cgi'

    def acknowledge_service(self, host, service, comment):
        payload = {
                'cmd_typ' : 34,
                'cmd_mod' : 2,
                'com_author' : self.user,
                'com_data' : comment,
                'host' : host,
                'service' : service,
                'send_notification' : True,
                'persistent' : False,
                'sticky_ack' : True
                }
        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def unacknowledge_service(self, host, service):
        payload = {
                'cmd_typ' : 52,
                'cmd_mod' : 2,
                'host' : host,
                'service' : service
                }
        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def schedule_service_downtime(self, host, service, options):
        payload = {
                'cmd_mod' : 2,
                'cmd_typ' : 56,
                'com_author' : options.get('author') or "%s via nagiosharder" % self.user,
                'com_data' : options.get('comment') or 'scheduled downtime by nagiosharder',
                'host' : host,
                'service' : service,
                'trigger' : 0,
                'type': 1
                }
        if options.get('type') == 'flexible':
            payload['fixed'] = 0
            payload['hours'] = options.get('hours') or 1
            payload['minutes'] = options.get('minutes') or 0

        payload['start_time'] = self.strftime(options.get('start_time') or datetime.now())
        payload['end_time'] = self._strftime(options.get('end_time')
                                            or datetime.now() + timedelta(hours=1))

        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def schedule_host_downtime(self, host, options):
        payload = {
                'cmd_mod' : 2,
                'cmd_typ' : 55,
                'com_author' : options.get('author' ) or "%s via nagiosharder" % self.user,
                'com_data' : options.get('comment') or 'scheduled downtime by nagiosharder',
                'host' : host,
                'childoptions' : 0,
                'trigger' : 0,
                'type': 1
                }
        if options.get('type') == 'flexible':
            payload['fixed'] = 0
            payload['hours'] = options.get('hours') or 1
            payload['minutes'] = options.get('minutes') or 0

        payload['start_time'] = self.strftime(options.get('start_time') or datetime.now())
        payload['end_time'] = self._strftime(options.get('end_time')
                                            or datetime.now() + timedelta(hours=1))

        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def cancel_downtime(self, downtime_id, dowtime_type='host_downtime'):
        dowtime_type = {
                'host_downtime' : 78,
                'service_downtime' : 79
                }.get('dowtime_type')
        payload = {
                'cmd_typ': dowtime_type,
                'cmd_mod': 2,
                'down_id': downtime_id
                }
        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def schedule_host_check(self, host, service):
        payload = {
                'start_time': self._strftime(datetime.now()),
                'host': host,
                'service': service,
                'force_check': True,
                'cmd_typ': 7,
                'cmd_mod': 2
                }
        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def schedule_service_check(self, host, service):
        payload = {
                'start_time' : self._strftime(datetime.now()),
                'host' : host,
                'service' : service,
                'force_check' : True,
                'cmd_typ' : 7,
                'cmd_mod' : 2
                }
        return requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)

    def service_status(self, type, options):
        service_status_type = {'ok': 2,
                'warning': 4,
                'unknown': 8,
                'critical': 16,
                'pending': 1,
                'all_problems': 28}.get(type) or None
        sort_type = None
        if 'sort_type' in options:
            sort_type = {'asc': 1, 'desc': 2}.get(options['sort_type']) or None

        sort_option = None
        if 'sort_option' in options:
            sort_option = {'host' : 1,
                    'service' : 2,
                    'status' : 3,
                    'last_check' : 4,
                    'duration' : 6,
                    'attempts' : 5}.get(options['sort_option']) or None

            service_group = options.get('group')
        payload = {
               'hoststatustype': options.get('hoststatustype') or 15,
               'servicestatustypes': options.get('servicestatustypes') or service_status_type,
               'sorttype': options.get('sorttype') or sort_type,
               'sortoption': options.get('sortoption') or sort_option,
               'hoststatustypes': options.get('hoststatustypes'),
               'serviceprops': options.get('serviceprops')
               }
        if self.version == 3:
            payload['servicegroup'] = service_group or 'all'
            payload['style'] = 'detail'
        else:
            if service_group:
                payload['servicegroup'] = service_group
                payload['style'] = 'detail'
            else:
                payload['host'] = 'all'
        query = urlencode(payload)
        url = "%s/%s" % (self.status_url, query)
        response = requests.get(url, auth=(self.user, self.password), verify=False)
        if response.ok:
            return parse_status_html(response.text)

    def host_status(self, host):
        host_status_url = "%s?host=%s" % (self.status_url, host)
        response = requests.get(host_status_url, auth=(self.user, self.password), verify=False)

        if response.ok:
            services = {}
            for status in parse_status_html(response.text):
                services[status['service']] = status
            return services

    def disable_service_notifications(self, host, service, options):
        payload = { 'cmd_mod': 2, 'host': host }
        if service:
            payload['cmd_typ'] = 23
            payload['service'] = service
        else:
            payload['cmd_typ'] = 29
            payload['ahas'] = True
        response = requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)
        if response.ok and 'successful' in response.text:
            return True
        else:
            return False

    def enable_service_notifications(self, host, service, options):
        payload = { 'cmd_mod': 2, 'host': host }
        if service:
            payload['cmd_typ'] = 22
            payload['service'] = service
        else:
            payload['cmd_typ'] = 28
            payload['ahas'] = True
        response = requests.post(self.cmd_url, auth=(self.user, self.password),
                                                    data=payload, verify=False)
        if response.ok and 'successful' in response.text:
            return True
        else:
            return False

    def _strftime(self, time):
        return datetime.strftime(self.nagios_time_format, time)