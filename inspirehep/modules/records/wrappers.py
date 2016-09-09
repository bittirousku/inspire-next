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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with INSPIRE. If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

from __future__ import absolute_import, division, print_function

from inspirehep.utils.record import get_title
from inspirehep.modules.records.es_record import ESRecord
from inspirehep.modules.search import JobsSearch


class LiteratureRecord(ESRecord):
    """Record class specialized for literature records."""

    @property
    def title(self):
        """Get preferred title."""
        return get_title(self)


class AuthorsRecord(ESRecord):
    """Record class specialized for author records."""

    @property
    def title(self):
        """Get preferred title."""
        return self.get('name', {}).get('preferred_name')


class ConferencesRecord(ESRecord):
    """Record class specialized for conference records."""

    @property
    def title(self):
        """Get preferred title."""
        return get_title(self)


class JobsRecord(ESRecord):
    """Record class specialized for job records."""

    @property
    def title(self):
        """Get preferred title."""
        return self.get('position')

    @property
    def similar(self):
        def _build_query(id_):
            result = JobsSearch()
            return result.query({
                'more_like_this': {
                    'docs': [
                        {
                            '_id': id_,
                        },
                    ],
                    'min_term_freq': 0,
                    'min_doc_freq': 0,
                }
            })[0:2]

        query = _build_query(self.get('control_number'))
        result = query.execute()

        return result


class InstitutionsRecord(ESRecord):
    """Record class specialized for institution records."""

    @property
    def title(self):
        """Get preferred title."""
        institution = self.get('institution')
        if institution:
            return institution[0]


class ExperimentsRecord(ESRecord):
    """Record class specialized for experiment records."""

    @property
    def title(self):
        """Get preferred title."""
        experiment_names = self.get('experiment_names')
        if experiment_names:
            return experiment_names[0].get('title')


class JournalsRecord(ESRecord):
    """Record class specialized for journal records."""

    @property
    def title(self):
        """Get preferred title."""
        return get_title(self)

    @property
    def short_title(self):
        """Get preferred title."""
        short_titles = self.get('short_titles', [])
        if short_titles:
            return short_titles[0].get('title', '')

    @property
    def publisher(self):
        """Get preferred title."""
        publisher = self.get('publisher', [])
        if publisher:
            return publisher[0]

    @property
    def urls(self):
        """Get urls."""
        urls = self.get('urls', [])
        if urls:
            return [url.get('value', '') for url in urls]

    @property
    def name_variants(self):
        """Get name variations."""
        name_variants = self.get('title_variants', [])
        if name_variants:
            return [name.get('title', '') for name in name_variants]