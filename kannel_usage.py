#!/usr/bin/env python
# encoding: utf-8

""" Quick & *very* dirty Kannel Access Log parser

outputs to either text or HTML """

import os
import sys
import re
import shutil
import math
import locale
from datetime import datetime

# configuration
TMP_FOLDER = '/tmp'
UNKNOWN = 'unknown'
SMS_PRICE = 20
KANNEL_LOG = '/var/log/kannel/access.log'
SMS_CHAR = 160.0
SMS_UNICHAR = 70.0

# regexp for matching messages with project.
# prefix name with priority matching (first match only)
SERVICES = {
    '2_pnlp': [r'^palu\ .+', ],
    '1_sharedsolar': [r'^([0-9]+|on|off)\..+', r'^\(.+'],
    '3_childcount': [r'^[a-zA-Z0-9]{3,6}\ \+.+', r'^[a-zA-Z]{3,}.*']
}

# template definitions
TEXT_ROOT = """
SMS ACCOUNTING:
%(months)s """
TEXT_MONTH = """    %(name)s
        %(valid)d SMS | %(error)d errors | %(total)d TOTAL | %(pays)sF

%(projects)s """
TEXT_PROJECT = """      %(name)s: %(usage)d SMS | %(bill)d | **%(pays)sF** """
HTML_ROOT = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<title>Earth Institute Mali SMS Gateway Statistics</title>
<style type="text/css">
body {
    font-family: sans-serif;
}
tr, td, th {
    border: solid 1px #333333;
}
th {
    background-color: #666666;
}

td, th {
    padding: 1em;
    text-align: left;
}

tr.total *, tr.month * {
    font-weight: bold;
}

tr.month td {
    text-align: center;
}
</style>
</head>
<body>
<h1>SMS ACCOUNTING</h1>
<p>Generated On %(date)s</p>
<table>
<tr><th>Project</th><th>Usage</th><th>Total</th><th>Amount FCFA</th><th>Errors</th></tr>
%(months)s
</table>
</body></html>"""
HTML_MONTH = """<tr class="month"><td colspan="5">%(name)s</td>
%(projects)s
<tr class="total"><td>TOTAL</td><td>%(valid)d</td><td>%(total)d</td><td>%(pays)sF</td><td>%(error)d<td></tr>
</tr>"""
HTML_PROJECT = """
<tr><td>%(name)s</td><td>%(usage)d</td><td>%(bill)d</td><td>%(pays)sF</td><td>n/a</td></tr>"""

# templates format switcher
TEMPLATES = {
    'text': {'root': TEXT_ROOT, 'month': TEXT_MONTH, 'project': TEXT_PROJECT},
    'html': {'root': HTML_ROOT, 'month': HTML_MONTH, 'project': HTML_PROJECT}}


class Counter(object):
    """ dict-like hold data """
    def __init__(self):
        self.projects = {}
        self.monthly = {}

    def add(self, month, project, nb=1):
        self._add('projects', project, month, nb)
        self._add('monthly', month, project, nb)

    def _add(self, key, key1, key2, nb):
        data = getattr(self, key)
        if not key1 in data:
            data[key1] = {}
        if not key2 in data[key1]:
            data[key1][key2] = 0
        data[key1][key2] += 1

    def by_month(self):
        return self.monthly

    def by_project(self):
        return self.projects


def copy_log(path='/var/log/kannel/access.log'):
    dest = os.path.join(TMP_FOLDER, 'access_%s.log' \
                                     % datetime.now().strftime('%s'))
    shutil.copyfile(path, dest)
    return dest


def project_for_message(message):
    """ loops on SERVICES to find project matching message or UNKNOWN """
    services = SERVICES.items()
    services.sort()
    for project, regexps in services:
        for regexp in regexps:
            if re.match(regexp, message, flags=re.IGNORECASE):
                return project.split('_', 1)[1]
    return UNKNOWN


def sms_num_for(text, length):
    """ guesses number of SMS consumed for that message """
    try:
        unicode(text).decode('ascii')
        return math.ceil(length / SMS_CHAR)
    except UnicodeDecodeError:
        return math.ceil(length / SMS_UNICHAR)
    return (length / SMS_CHAR)


def msg_for_line(line):
    """ msg dict for a log line """
    msg = {}

    data = [text.rsplit(']', 1)[0] for text in line.split('[')]

    command = data[0].split(' ', 2)[-1].lower()
    if command.startswith('receive'):
        msg['direction'] = 'incoming'
    elif command.startswith('sent'):
        msg['direction'] = 'outgoing'
    elif command.startswith('failed'):
        msg['direction'] = 'outgoing'
    else:
        return None

    msg['month'] = data[0].split()[0][:-3]
    msg['len'] = int(data[9].split(':', 2)[1])
    user = data[2].split(':', 1)[1]
    text = data[9].split(':', 2)[2]
    if user:
        msg['project'] = user
    else:
        msg['project'] = project_for_message(text)
    msg['nb_sms'] = sms_num_for(text, msg['len'])
    return msg


def read(path):
    log = open(path)

    count = Counter()

    for line in log.readlines():
        line = line.strip()
        if line.lower().split()[2] == 'log':
            continue
        msg = msg_for_line(line)
        if msg:
            count.add(msg['month'], msg['project'], msg['nb_sms'])

    return billing(count)


def billing(count):
    """ a dictionary index by month with billing data """

    bill = {}

    for month, data in count.by_month().items():

        # month total data
        try:
            errors = count.by_project()[UNKNOWN][month]
        except IndexError:
            errors = 0
        total_sms = sum(count.by_month()[month].values())
        no_error = total_sms - errors
        amount = total_sms * SMS_PRICE
        bill[month] = {'error': errors, 'valid': no_error, \
                       'total': total_sms, 'pay': amount, \
                       'pays': locale.format("%d", amount, grouping=True),
                       'projects': {}}

        for project, nb in data.items():
            if project == UNKNOWN:
                continue

            # calculate error share
            my_error_rate = nb * 100.0 / no_error
            my_error = math.ceil(errors * my_error_rate / 100.0)
            mysms = nb + my_error
            myprice = mysms * SMS_PRICE

            bill[month]['projects'][project] = {'name': project, 'usage': nb, \
                                                'bill': mysms, \
                                                'pay': myprice, \
                                                'pays': locale.format("%d", myprice, grouping=True)}

    return bill


def output_text(bill, format='text'):
    tpl = TEMPLATES[format.lower()]

    months = []
    for month, month_data in bill.items():

        projects = []
        for project, project_data in month_data['projects'].items():
            projects.append(tpl['project'] % project_data)
        projects_text = "\n".join(projects)

        months.append(tpl['month'] % {'name': month, 'pay': month_data['pay'], \
                                      'pays': locale.format("%d", \
                                                            month_data['pay'], \
                                                            grouping=True), \
                                      'valid': month_data['valid'], \
                                      'error': month_data['error'], \
                                      'total': month_data['total'], \
                                      'projects': projects_text})
    months_text = "\n".join(months)

    return tpl['root'] % {'months': months_text, 'date': datetime.now().strftime('%c')}


def main():
    locale.setlocale(locale.LC_ALL, '')

    if sys.argv.__len__() > 1 and sys.argv[1].replace('-','') in ['h', 'html']:
        format = 'html'
    else:
        format = 'text'

    if len(sys.argv) >= 3:
        path = sys.argv[2]
    else:
        path = copy_log(KANNEL_LOG)

    bill = read(path)
    print(output_text(bill, format))

if __name__ == '__main__':
    main()
