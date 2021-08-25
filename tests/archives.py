# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, see <http://www.gnu.org/licenses/>.


from koji import PathInfo
from unittest import TestCase
from unittest.mock import MagicMock

from kojismokydingo.archives import (
    as_pathinfo,
    gather_build_archives, gather_build_maven_archives, gather_build_rpms, )


ARCHIVE_BUILD = {
    'build_id': 8675309,
    'id': 8675309,
    'cg_id': None,
    'cg_name': None,
    'completion_time': '2011-10-20 17:34:29.213107',
    'completion_ts': 1319132069.21311,
    'creation_event_id': 4337236,
    'creation_time': '2011-10-20 17:32:57.164980',
    'creation_ts': 1319131977.16498,
    'epoch': None,
    'extra': None,
    'name': 'org.apache.maven-maven',
    'nvr': 'org.apache.maven-maven-3.0.3-5',
    'owner_id': 2,
    'owner_name': 'somebody_cool',
    'package_id': 10849,
    'package_name': 'org.apache.maven-maven',
    'release': '5',
    'source': None,
    'start_time': None,
    'start_ts': None,
    'state': 1,
    'task_id': 3728626,
    'version': '3.0.3',
    'volume_id': 0,
    'volume_name': 'DEFAULT',
}


ARCHIVE_RPMS = [
    { 'arch': 'src',
      'build_id': 8675309,
      'buildroot_id': 1109499,
      'buildtime': 1319146436,
      'epoch': None,
      'external_repo_id': 0,
      'external_repo_name': 'INTERNAL',
      'extra': None,
      'id': 2032164,
      'metadata_only': False,
      'name': 'maven3',
      'nvr': 'maven3-3.0.3-5',
      'payloadhash': '345c9aa86bf2578ba0479bc9b6186651',
      'release': '5',
      'size': 30692341,
      'version': '3.0.3', },

    { 'arch': 'noarch',
      'build_id': 8675309,
      'buildroot_id': 1109499,
      'buildtime': 1319146438,
      'epoch': None,
      'external_repo_id': 0,
      'external_repo_name': 'INTERNAL',
      'extra': None,
      'id': 2032165,
      'metadata_only': False,
      'name': 'maven3',
      'nvr': 'maven3-3.0.3-5',
      'payloadhash': '34bb9f04c1deb68a740835fc4e1554de',
      'release': '5',
      'size': 3330775,
      'version': '3.0.3', },
]

ARCHIVE_MAVEN = [
    { 'artifact_id': 'maven',
      'btype': 'maven',
      'btype_id': 2,
      'build_id': 8675309,
      'buildroot_id': 12345,
      'checksum': 'd485573048f68a88769a4b3dc1ade6bd',
      'checksum_type': 0,
      'extra': None,
      'filename': 'org.apache.maven-maven-3.0.3-sources.zip',
      'group_id': 'org.apache.maven',
      'id': 123937,
      'metadata_only': False,
      'size': 11967141,
      'type_description': 'Zip file',
      'type_extensions': 'zip',
      'type_id': 2,
      'type_name': 'zip',
      'version': '3.0.3', },
    { 'artifact_id': 'maven-core',
      'btype': 'maven',
      'btype_id': 2,
      'build_id': 8675309,
      'buildroot_id': 12345,
      'checksum': '0c6c08c75c68ebacc3844f1b5997e7d6',
      'checksum_type': 0,
      'extra': None,
      'filename': 'maven-core-3.0.3.jar',
      'group_id': 'org.apache.maven',
      'id': 123978,
      'metadata_only': False,
      'size': 590478,
      'type_description': 'Jar file',
      'type_extensions': 'jar war rar ear sar kar jdocbook jdocbook-style plugin',
      'type_id': 1,
      'type_name': 'jar',
      'version': '3.0.3', },
    { 'artifact_id': 'maven-core',
      'btype': 'maven',
      'btype_id': 2,
      'build_id': 8675309,
      'buildroot_id': 12345,
      'checksum': '58098887fbae29abb3e7ef52de833f64',
      'checksum_type': 0,
      'extra': None,
      'filename': 'maven-core-3.0.3.pom',
      'group_id': 'org.apache.maven',
      'id': 123979,
      'metadata_only': False,
      'size': 6401,
      'type_description': 'Maven Project Object Management file',
      'type_extensions': 'pom',
      'type_id': 3,
      'type_name': 'pom',
      'version': '3.0.3', },
]


class TestBuildArchives(TestCase):

    def get_session(self):

        session = MagicMock()

        session.getBuild.side_effect = [ARCHIVE_BUILD, ]
        session.getBuildType.side_effect = [['rpm', 'maven',], ]

        session.listRPMs.side_effect = [ARCHIVE_RPMS, ]

        def listArchives(buildID, type=None):
            if type == "maven":
                return ARCHIVE_MAVEN
            else:
                return []

        session.listArchives.side_effect = listArchives

        return session


    def test_gather_build_archives(self):

        session = self.get_session()

        res = gather_build_archives(session,
                                    "org.apache.maven-maven-3.0.3-5",
                                    path="/testing")

        self.assertEqual(len(res), 5)

        session = self.get_session()

        res = gather_build_archives(session,
                                    "org.apache.maven-maven-3.0.3-5",
                                    btype="win",
                                    path="/testing")

        self.assertEqual(len(res), 0)


    def test_gather_build_rpms(self):

        session = self.get_session()

        res = gather_build_archives(session,
                                    "org.apache.maven-maven-3.0.3-5",
                                    btype="rpm",
                                    path="/testing")

        self.assertEqual(len(res), 2)

        session = self.get_session()

        res = gather_build_rpms(session,
                                "org.apache.maven-maven-3.0.3-5", (),
                                path="/testing")

        self.assertEqual(len(res), 2)


    def test_gather_build_maven(self):

        session = self.get_session()

        res = gather_build_archives(session,
                                    "org.apache.maven-maven-3.0.3-5",
                                    btype="maven",
                                    path="/testing")

        self.assertEqual(len(res), 3)

        session = self.get_session()

        res = gather_build_maven_archives(session,
                                          "org.apache.maven-maven-3.0.3-5",
                                          path="/testing")

        self.assertEqual(len(res), 3)


class TestPathInfo(TestCase):

    def test_as_pathinfo(self):

        pi = as_pathinfo("/foo")

        self.assertEqual(type(pi), PathInfo)
        self.assertEqual(pi.topdir, "/foo")

        self.assertTrue(pi is as_pathinfo(pi))


#
# The end.
