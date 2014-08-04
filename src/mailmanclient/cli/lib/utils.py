#!/usr/bin/python

# Copyright (C) 2010-2014 by the Free Software Foundation, Inc.
#
# This file is part of mailman.client.
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailman.client is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

import re
import sys
import csv
from hashlib import sha1
from datetime import datetime


class Utils():
    """ General utilities to be used across the CLI """

    # Give colored output on the CLI"
    def warn(self, message):
        print "\033[94m%s\033[0m" % message

    def error(self, message):
        sys.stderr.write("\033[91m%s\033[0m\n" % message)

    def confirm(self, message):
        print "\033[94m%s\033[0m" % message,

    def emphasize(self, message):
        print "\033[94m%s\033[0m" % message

    def return_emphasize(self, message):
        return "\033[92m%s\033[0m" % message
    # End Colors!

    def get_random_string(self, length):
        """ Returns short random strings, less than 40 bytes in length.

        :param length: Length of the random string to be returned
        :type length: int
        """
        try:
            return sha1(str(datetime.now())).hexdigest()[:length]
        except IndexError:
            raise Exception('Specify length less than 40')

    def set_table_section_heading(self, table, heading):
        table.append(['', ''])
        table.append([heading, ''])
        table.append(['=============', ''])

    def write_csv(self, table, headers, filename):
        if table == []:
            return
        if 'csv' not in filename:
            filename += '.csv'
        f = open(filename, 'wb')
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        if headers:
            writer.writerow(headers)
        for row in table:
            writer.writerow(row)
        f.close()
        return

    def stem(self, arguments):
        """ Allows the scope to be in singular or plural

        :param arguments: The sys.argv, passed from mmclient
        :type arguments: list
        """
        scope = arguments[2]
        if scope[-1] == 's':
            scope = scope[:-1]
        arguments[2] = scope
        return arguments


class Filter():
    key = None
    value = None
    operator = None
    data_set = []
    utils = Utils()

    def __init__(self, key, value, operator, data):
        self.key = key
        self.value = value
        self.operator = operator
        self.data_set = data

    def get_results(self):
        if self.operator == '=':
            return self.equality()
        elif self.operator == 'like':
            return self.like()
        elif self.operator == 'in':
            return self.in_list()
        else:
            raise Exception('Invalid operator: %s ' % (self.operator))

    def equality(self):
        copy_set = self.data_set[:]
        for i in self.data_set:
            try:
                obj_value = getattr(i, self.key)
                if obj_value != self.value:
                    copy_set.remove(i)
            except AttributeError:
                raise Exception('Invalid filter : %s' % self.key)
        return copy_set

    def in_list(self):
        copy_set = self.data_set[:]
        flag = False
        for i in self.data_set:
            try:
                try:
                    the_list = getattr(i, self.key)
                except KeyError:
                    copy_set.remove(i)
                    continue
                if self.key == 'members':
                    for j in the_list:
                        if self.match_pattern(j.email):
                            flag = True
                            break
                elif self.key == 'lists':
                    for j in the_list:
                        if (self.match_pattern(j.list_id)
                            or self.match_pattern(j.fqdn_listname)):
                            flag = True
                            break
                elif self.key == 'subscriptions':
                    self.value = self.value.replace('@', '.')
                    for j in the_list:
                        if self.match_pattern(j.list_id):
                            flag = True
                            break
                else:
                    for j in the_list:
                        if self.match_pattern(j):
                            flag = True
                            break
                if not flag:
                    copy_set.remove(i)
                flag = False
            except AttributeError:
                raise Exception('Invalid filter : %s' % self.key)
        return copy_set

    def like(self):
        copy_set = self.data_set[:]
        for i in self.data_set:
            try:
                obj_value = None
                try:
                    obj_value = getattr(i, self.key)
                except KeyError:
                    copy_set.remove(i)
                if not self.match_pattern(obj_value):
                    copy_set.remove(i)
            except AttributeError:
                if self.key not in ['domain', 'user', 'list']:
                    raise Exception('Invalid filter : %s' % self.key)
        return copy_set

    def match_pattern(self, string):
        pattern = None
        try:
            pattern = re.compile(self.value.lower())
        except:
            raise Exception('Invalid pattern : %s' % self.value)
        string = str(string).lower()
        return pattern.match(string)
