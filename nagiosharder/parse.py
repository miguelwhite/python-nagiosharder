from datetime import timedelta, datetime
import re
from logbook import Logger
from html import Html

log = Logger('parse')

# TODO:
# add down parsing
# cgi params explained
# http://docs.icinga.org/latest/en/cgiparams.html
# http://roshamboot.org/main/guide-nagios-statuscgi/

def parse_status_html(nagios_status_html_str):
    rows = Html(nagios_status_html_str).cssselect('table.status > tr')
    time_format = '%d-%m-%Y %H:%M:%S'
    for row in rows[1:]:
        res =  parse_status_html_row(time_format, row)
        if res:
            yield res


def parse_status_html_row(time_format, row):
    item = {
            'host': None,
            'host_extinfo_url': None,
            'service': None,
            'status': None,
            'last_check': None,
            'duration': None,
            'attempts': None,
            'started_at': None,
            'extended_info': None,
            'acknowledged': None,
            'service_extinfo_url': None,
            'comments_url': None,
            'extra_service_notes_urls': None,
            'notifications_disabled': None,
            'passive_only': None
            }
    columns = row.getchildren()
    if not columns or len(columns) == 1:
        return
    item['host'] = columns[0].text_content().replace('\n', '')
    def _find_host_name(node):
        hostname = node.getprevious().getchildren()[0].text_content().replace('\n', '')
        while not hostname:
            node = node.getprevious()
            hostname = node.getprevious().getchildren()[0].text_content().replace('\n', '')
        return hostname

    if not item['host']:
        item['host'] = _find_host_name(row)

    links = columns[0].cssselect('td a')
    links += columns[1].cssselect('td a')
    if len(links) > 1:
        item['extinfo_url'] = find_link(lambda s: s.get('href').startswith('extinfo.cgi'), links)
        item['comments_url'] = find_link(lambda s: s.get('href').endswith('comments'), links)

        imgs_nodes = [x.cssselect('img')[0] for x in links if x.cssselect('img')]
        imgs = [x.get('src') for x in imgs_nodes]
        item['acknowledged'] = bool_none(x for x in imgs if 'ack.gif' in x)
        item['passive_only'] = bool_none(x for x in imgs if 'passiveonly.gif' in x)
        item['notifications_disabled'] = bool_none(x for x in imgs if 'disabled.gif' in x)

        extra_service_notes_link = [x for x in imgs_nodes if 'notes.gif' in x.get('src')]
        if extra_service_notes_link:
            item['extra_service_notes_urls'] = [x.getparent().get('href') for x in extra_service_notes_link]

    item['service'] = columns[1].cssselect('a')[0].text

    if len(columns) > 2:
        item['status'] = columns[2].text.strip()

    if len(columns) > 3:
        last_check = item['last_check'] = columns[3].text # FIXME: convert to common format

    if len(columns) > 4:
        duration = item['duration'] = columns[4].text.strip()
        started_at = dict(zip(('days', 'hours', 'minutes', 'seconds'), sift_none(map(parse_int, duration.split(' ')))))
        item['started_at'] = time_diff(time_format, last_check, timedelta(**started_at))

    if len(columns) > 5:
        item['attempts'] = columns[5].text

    if len(columns) > 6:
        item['status_info'] = columns[6].text[:-1]

    return item


def find_link(pred, seq):
    res = filter(pred, seq)
    if res:
        return res[0].get('href')

def sift_none(seq):
    return [x for x in seq if x is not None]

def parse_int(string):
    found = re.findall('[0-9]+', string)
    if found:
        return int(found[0])

def time_diff(fmt, start, delta):
    return (datetime.strptime(start, fmt) - delta).strftime(fmt)

def bool_none(x):
    if hasattr(x, 'next'):
        x = list(x)
    if x is not None:
        return bool(x)
