# -*- coding: utf-8 -*-
#
# This file is part of INSPIRE.
# Copyright (C) 2016 CERN.
#
# INSPIRE is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# INSPIRE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

"""References Processors."""

import re

import idutils
from isbn import ISBNError

from inspirehep.utils.pubnote import split_pubnote


def _is_arxiv(obj):
    """Small checker for arXiv report numbers."""
    # Workaround until this issue:
    # https://github.com/inveniosoftware/idutils/issues/14 is solved.

    arxiv_test = obj.split()
    if not arxiv_test:
        return False
    return idutils.is_arxiv(arxiv_test[0])


def _normalize_arxiv(obj):
    """Normalize arXiv report numbers accepted by _is_arxiv."""
    return idutils.normalize_arxiv(obj.split()[0])


class ReferenceBuilder(object):
    """Class used for building JSON reference objects given simple properties.

    Use this when:
        * Converting from MARC to Literature
        * Parsing refextract output
        * Pushing a record from Holdingpen

    We wrote this in a non-pythonic non-generic way so it's extensible to any
    format a reference field might take.
    """

    RE_VALID_CNUM = re.compile(r'C\d{2}-\d{2}-\d{2}(\.\d+)?')
    RE_VALID_PUBNOTE = re.compile(r'.*,.*,.*(,.*)?')

    def __init__(self):
        self.obj = {}

    def _ensure_field(self, field_name, value):
        if field_name not in self.obj:
            self.obj[field_name] = value

    def set_number(self, number):
        try:
            self.obj['number'] = int(number)
        except (ValueError, TypeError):
            pass

    def set_record(self, record):
        self.obj['record'] = record
        self._ensure_field('curated_relation', False)

    def curate(self):
        self.obj['curated_relation'] = True

    def set_texkey(self, texkey):
        self.obj['texkey'] = texkey

    def add_title(self, title):
        self._ensure_field('titles', [])
        self.obj['titles'].append({'value': title})

    def add_misc(self, misc):
        self._ensure_field('misc', [])
        self.obj['misc'].append(misc)

    def add_raw_reference(self, raw_reference, serialization='text'):
        self._ensure_field('raw_reference', [])
        self.obj['raw_reference'].append({
            'value': raw_reference,
            'serialization': serialization})

    def set_year(self, year):
        try:
            year = int(year)
        except (ValueError, TypeError):
            return
        if year >= 1000 and year <= 2050:
            self._ensure_field('publication_info', {})
            self.obj['publication_info']['year'] = year

    def add_url(self, url):
        self._ensure_field('urls', [])
        self.obj['urls'].append({'value': url})

    def add_author(self, full_name, role=None):
        self._ensure_field('authors', [])
        author = {} if not role else {'role': role}
        author['full_name'] = full_name
        self.obj['authors'].append(author)

    def set_pubnote(self, pubnote):
        """Parse pubnote and populate correct fields."""
        if self.RE_VALID_PUBNOTE.match(pubnote):
            values = split_pubnote(pubnote)
            keys = (
                'journal_title',
                'journal_volume',
                'page_start',
                'page_end',
                'artid')
            self._ensure_field('publication_info', {})
            for idx, key in enumerate(keys):
                if values[idx]:
                    self.obj['publication_info'][key] = values[idx]
        else:
            self.add_raw_reference(pubnote)

    def set_publisher(self, publisher):
        self._ensure_field('imprint', {})
        self.obj['imprint']['publisher'] = publisher

    def add_report_number(self, repno):
        # For some reason we get more recall by trying the first part in
        # splitting the report number.
        repno = repno or ''
        if _is_arxiv(repno):
            self._ensure_field('arxiv_eprints', [])
            self.obj['arxiv_eprints'].append(_normalize_arxiv(repno))
        else:
            self._ensure_field('publication_info', {})
            self.obj['publication_info']['reportnumber'] = repno

    def add_uid(self, uid):
        """Add unique identifier in correct field."""
        # We might add None values from wherever. Kill them here.
        uid = uid or ''
        if _is_arxiv(uid):
            self._ensure_field('arxiv_eprints', [])
            self.obj['arxiv_eprints'].append(_normalize_arxiv(uid))
        elif idutils.is_doi(uid):
            self._ensure_field('publication_info', {})
            self.obj['publication_info']['doi'] = idutils.normalize_doi(uid)
        elif idutils.is_handle(uid):
            self._ensure_field('persistent_identifiers', [])
            value = idutils.normalize_handle(uid)
            if not value.startswith('hdl:'):
                # Prone to the day in which normalize_handle might prepend
                # 'hdl:'.
                value = 'hdl:{}'.format(value)
            self.obj['persistent_identifiers'].append(value)
        elif self.RE_VALID_CNUM.match(uid):
            self._ensure_field('publication_info', {})
            self.obj['publication_info']['cnum'] = uid
        else:
            # idutils.is_isbn has a different implementation than normalize
            # isbn. Better to do it like this.
            try:
                isbn = idutils.normalize_isbn(uid)
                self._ensure_field('publication_info', {})
                self.obj['publication_info']['isbn'] = isbn
            except ISBNError:
                pass

    def add_collaboration(self, collaboration):
        self._ensure_field('collaboration', [])
        self.obj['collaboration'].append(collaboration)