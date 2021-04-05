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


import koji

from collections import OrderedDict
from mock import MagicMock, PropertyMock, patch
from unittest import TestCase

from kojismokydingo import (
    BadDingo, FeatureUnavailable,
    NoSuchBuild, NoSuchTag, NoSuchTarget, NoSuchUser,
    as_buildinfo, as_taginfo, as_targetinfo, as_userinfo,
    bulk_load, iter_bulk_load,
    version_check, version_require, )


class TestIterBulkLoad(TestCase):

    def setUp(self):
        self.prep = patch('koji.ClientSession._prepCall').start()
        self.prep.return_value = (None, None, None)
        self.send = patch('koji.ClientSession._sendCall').start()
        self.session = koji.ClientSession('FAKE_URL')


    def tearDown(self):
        patch.stopall()


    def test_iter_bulk_load(self):
        # validates that the iter_bulk_load utility is indeed breaking up
        # the list of keys into the appropriate sized chunks and
        # invoking the function in a multicall loop, then yielding the
        # key:result pairs.

        # these are our pretend results for the expected multicall
        # invocations.
        self.send.side_effect = [
            [[100 + v] for v in range(i, i+5)] for i in range(0, 25, 5)
        ]

        x = iter_bulk_load(self.session, self.session.ImpossibleDream,
                           range(0, 25), True, size=5)
        x = list(x)

        self.assertEqual(x, list(zip(range(0, 25), range(100, 125))))

        self.assertEqual(self.prep.call_count, 5)
        self.assertEqual(self.send.call_count, 5)

        # we'll validate that the prep mock was triggered five times, each
        # with five invocations to the ImpossibleDream endpoint, with a
        # single incrementing integer argument.
        for prep, offset in zip(self.prep.call_args_list, range(0, 25, 5)):

            # the multicall invocation itself
            mc = prep[0]
            self.assertEqual(mc[0], "multiCall")

            # the first argument to the multiCall invocation is a list
            # of endpoints to call and the args
            calls = mc[1][0]
            self.assertEqual(len(calls), 5)

            for i, call in enumerate(calls):
                self.assertEqual(call['methodName'], "ImpossibleDream")
                self.assertEqual(call['params'], (i + offset,))


class TestBulkLoad(TestCase):


    def session(self, data):
        inputs = []

        def _convert_dat(i):
            v = data[i]
            if isinstance(v, dict) and "faultCode" in v:
                return v
            else:
                return [v]

        def do_call(value):
            inputs.append(value)

        def do_mc(strict=None):
            results = [_convert_dat(i) for i in inputs]
            inputs[:] = ()  # python2 doesn't have list.clear()
            return results

        sess = MagicMock()

        dream = sess.ImpossibleDream
        dream.side_effect = do_call

        mc = sess.multiCall
        mc.side_effect = do_mc

        return sess


    def fault(self, code=koji.GenericError.faultCode, msg="ohnoes"):
        return {"faultCode": code, "faultString": msg}


    def test_iter_bulk_load(self):
        data = OrderedDict((val, "dream %i" % val) for val in range(0, 100))
        expect = OrderedDict(data)

        sess = self.session(data)

        res = iter_bulk_load(sess, sess.ImpossibleDream,
                             data, size=5)

        for (key, val), hope in zip(res, data):
            self.assertEqual(key, hope)
            self.assertEqual(expect[key], val)

        self.assertEqual(sess.ImpossibleDream.call_count, 100)
        self.assertEqual(sess.multiCall.call_count, 20)


    def test_iter_bulk_load_err(self):
        data = {
            "1": "one",
            "2": self.fault(),
            "3": "three",
            "4": None,
        }

        sess = self.session(data)
        res = iter_bulk_load(sess, sess.ImpossibleDream, "1234", err=False)
        self.assertEqual(next(res), ("1", "one"))
        self.assertEqual(next(res), ("2", None))
        self.assertEqual(next(res), ("3", "three"))
        self.assertEqual(next(res), ("4", None))
        self.assertRaises(StopIteration, next, res)

        sess = self.session(data)
        res = iter_bulk_load(sess, sess.ImpossibleDream, "1234", err=True)
        self.assertEqual(next(res), ("1", "one"))
        self.assertRaises(koji.GenericError, next, res)
        self.assertRaises(StopIteration, next, res)


    def test_bulk_load(self):
        data = OrderedDict((val, "dream %i" % val) for val in range(0, 100))
        expect = OrderedDict(data)

        sess = self.session(data)

        res = bulk_load(sess, sess.ImpossibleDream,
                        data, size=5)

        self.assertTrue(isinstance(res, OrderedDict))
        self.assertEqual(res, expect)
        self.assertEqual(sess.ImpossibleDream.call_count, 100)
        self.assertEqual(sess.multiCall.call_count, 20)


    def test_bulk_load_err(self):
        data = {
            "1": "one",
            "2": self.fault(),
            "3": "three",
            "4": None,
        }

        sess = self.session(data)
        res = bulk_load(sess, sess.ImpossibleDream, "1234", err=False)
        self.assertTrue(isinstance(res, OrderedDict))

        res = iter(res.items())
        self.assertEqual(next(res), ("1", "one"))
        self.assertEqual(next(res), ("2", None))
        self.assertEqual(next(res), ("3", "three"))
        self.assertEqual(next(res), ("4", None))
        self.assertRaises(StopIteration, next, res)

        sess = self.session(data)
        self.assertRaises(koji.GenericError, bulk_load, sess,
                          sess.ImpossibleDream, "1234", err=True)


class TestVersionCheck(TestCase):

    def session(self, results):
        sess = MagicMock()

        send = sess.getKojiVersion
        send.side_effect = results

        return sess, send


    def ge(self):
        return koji.GenericError("Invalid method: getKojiVersion")


    def test_bad_version_check(self):

        sess, send = self.session(["1.25"])
        self.assertFalse(version_check(sess, "1.26"))
        self.assertFalse(version_check(sess, (1, 26)))
        self.assertFalse(version_check(sess, (1, 27)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 25))
        self.assertEqual(send.call_count, 1)

        sess, send = self.session([self.ge()])
        self.assertFalse(version_check(sess, (1, 23)))
        self.assertFalse(version_check(sess, (1, 24)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 22))
        self.assertEqual(send.call_count, 1)


    def test_good_version_check(self):

        sess, send = self.session(["1.24"])
        self.assertTrue(version_check(sess, "1.23"))
        self.assertTrue(version_check(sess, (1, 23)))
        self.assertTrue(version_check(sess, (1, 24)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 24))
        self.assertEqual(send.call_count, 1)

        sess, send = self.session(["1.25"])
        self.assertTrue(version_check(sess, (1, 24)))
        self.assertTrue(version_check(sess, (1, 25)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 25))
        self.assertEqual(send.call_count, 1)

        sess, send = self.session([self.ge()])
        self.assertTrue(version_check(sess, (1, 22)))
        self.assertTrue(version_check(sess, (1, 22)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 22))
        self.assertEqual(send.call_count, 1)


    def test_bad_version_require(self):

        sess, send = self.session(["1.25"])
        self.assertRaises(FeatureUnavailable, version_require, sess, (1, 26))
        self.assertRaises(FeatureUnavailable, version_require, sess, (1, 27))
        self.assertEqual(vars(sess)["__hub_version"], (1, 25))
        self.assertEqual(send.call_count, 1)

        sess, send = self.session([self.ge()])
        self.assertRaises(FeatureUnavailable, version_require, sess, (1, 23))
        self.assertRaises(FeatureUnavailable, version_require, sess, (1, 24))
        self.assertEqual(vars(sess)["__hub_version"], (1, 22))
        self.assertEqual(send.call_count, 1)


    def test_good_version_require(self):

        sess, send = self.session(["1.24"])
        self.assertTrue(version_require(sess, (1, 23)))
        self.assertTrue(version_require(sess, (1, 24)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 24))
        self.assertEqual(send.call_count, 1)

        sess, send = self.session(["1.25"])
        self.assertTrue(version_require(sess, (1, 24)))
        self.assertTrue(version_require(sess, (1, 25)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 25))
        self.assertEqual(send.call_count, 1)

        sess, send = self.session([self.ge()])
        self.assertTrue(version_require(sess, (1, 22)))
        self.assertTrue(version_require(sess, (1, 22)))
        self.assertEqual(vars(sess)["__hub_version"], (1, 22))
        self.assertEqual(send.call_count, 1)


class TestAsBuildInfo(TestCase):

    DATA = {
        "id": 1,
        "state": 2,
        "nvr": "sample-1-1",
    }


    def session(self, results):
        sess = MagicMock()

        send = sess.getBuild
        send.side_effect = results

        return sess, send


    def test_as_buildinfo_nvr(self):

        key = "sample-1-1"
        sess, send = self.session([self.DATA])
        res = as_buildinfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))


    def test_as_buildinfo_id(self):

        sess, send = self.session([self.DATA])
        res = as_buildinfo(sess, 1)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (1,))


    def test_as_buildinfo_dict(self):

        sess, send = self.session([])
        res = as_buildinfo(sess, self.DATA)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 0)


    def test_no_such_build(self):

        key = "sample-1-1"
        sess, send = self.session([None])
        self.assertRaises(NoSuchBuild, as_buildinfo, sess, key)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))

        sess, send = self.session([])
        self.assertRaises(NoSuchBuild, as_buildinfo, sess, None)
        self.assertEqual(send.call_count, 0)


class TestAsTaginfo(TestCase):

    DATA = {
        "id": 1,
        "name": "example-1.0-build",
    }


    def session(self, results, ver="1.23"):
        sess = MagicMock()

        send = sess.getTag
        send.side_effect = results

        vercheck = sess.getKojiVersion
        vercheck.side_effect = [ver]

        return sess, send


    def test_as_taginfo_name(self):

        key = "example-1.0-build"

        sess, send = self.session([self.DATA])
        res = as_taginfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))
        self.assertEqual(send.call_args_list[0][1], {"blocked": True})

        sess, send = self.session([self.DATA], ver="1.22")
        res = as_taginfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))
        self.assertEqual(send.call_args_list[0][1], {})


    def test_as_taginfo_id(self):

        sess, send = self.session([self.DATA])
        res = as_taginfo(sess, 1)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (1,))
        self.assertEqual(send.call_args_list[0][1], {"blocked": True})

        sess, send = self.session([self.DATA], ver="1.22")
        res = as_taginfo(sess, 1)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (1,))
        self.assertEqual(send.call_args_list[0][1], {})


    def test_as_taginfo_dict(self):

        sess, send = self.session([])
        res = as_taginfo(sess, self.DATA)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 0)


    def test_no_such_tag(self):

        key = "example-1.0-build"

        sess, send = self.session([None])
        self.assertRaises(NoSuchTag, as_taginfo, sess, key)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))
        self.assertEqual(send.call_args_list[0][1], {"blocked": True})

        sess, send = self.session([None], ver="1.22")
        self.assertRaises(NoSuchTag, as_taginfo, sess, key)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))
        self.assertEqual(send.call_args_list[0][1], {})

        sess, send = self.session([])
        self.assertRaises(NoSuchTag, as_taginfo, sess, None)
        self.assertEqual(send.call_count, 0)


class TestAsTargetInfo(TestCase):

    DATA = {
        "id": 1,
        "name": "example-1.0-candidate",
    }


    def session(self, results):
        sess = MagicMock()

        send = sess.getBuildTarget
        send.side_effect = results

        return sess, send


    def test_as_targetinfo_nvr(self):

        key = "example-1.0-candidate"
        sess, send = self.session([self.DATA])
        res = as_targetinfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))


    def test_as_targetinfo_id(self):

        sess, send = self.session([self.DATA])
        res = as_targetinfo(sess, 1)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (1,))


    def test_as_targetinfo_dict(self):

        sess, send = self.session([])
        res = as_targetinfo(sess, self.DATA)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 0)


    def test_no_such_build(self):

        key = "example-1.0-candidate"
        sess, send = self.session([None])
        self.assertRaises(NoSuchTarget, as_targetinfo, sess, key)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key,))

        sess, send = self.session([])
        self.assertRaises(NoSuchTarget, as_targetinfo, sess, None)
        self.assertEqual(send.call_count, 0)


class TestAsUserinfo(TestCase):

    DATA = {
        "id": 1,
        "name": "joey_ramone",
    }


    def session(self, results):
        sess = MagicMock()

        send = sess.getUser
        send.side_effect = results

        return sess, send


    def err(self):
        return koji.ParameterError()


    def test_as_userinfo_name(self):

        key = "joey_ramone"

        sess, send = self.session([self.DATA, self.DATA])
        res = as_userinfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key, False, True))

        sess_vars = vars(sess)
        self.assertTrue("__new_get_user" in sess_vars)
        self.assertTrue(sess_vars["__new_get_user"])

        res = as_userinfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[1][0], (key, False, True))

        sess, send = self.session([self.err(), self.DATA, self.DATA])
        res = as_userinfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[0][0], (key, False, True))
        self.assertEqual(send.call_args_list[1][0], (key,))

        sess_vars = vars(sess)
        self.assertTrue("__new_get_user" in sess_vars)
        self.assertFalse(sess_vars["__new_get_user"])

        res = as_userinfo(sess, key)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 3)
        self.assertEqual(send.call_args_list[2][0], (key,))


    def test_as_userinfo_id(self):

        sess, send = self.session([self.DATA])
        res = as_userinfo(sess, 1)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (1, False, True))

        sess, send = self.session([self.err(), self.DATA])
        res = as_userinfo(sess, 1)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[0][0], (1, False, True))
        self.assertEqual(send.call_args_list[1][0], (1,))


    def test_as_userinfo_dict(self):

        sess, send = self.session([])
        res = as_userinfo(sess, self.DATA)
        self.assertEqual(res, self.DATA)
        self.assertEqual(send.call_count, 0)


    def test_no_such_user(self):

        key = "joey_ramone"

        sess, send = self.session([None])
        self.assertRaises(NoSuchUser, as_userinfo, sess, key)
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args_list[0][0], (key, False, True))

        sess, send = self.session([self.err(), None])
        self.assertRaises(NoSuchUser, as_userinfo, sess, key)
        self.assertEqual(send.call_count, 2)
        self.assertEqual(send.call_args_list[0][0], (key, False, True))
        self.assertEqual(send.call_args_list[1][0], (key,))

        sess, send = self.session([])
        self.assertRaises(NoSuchUser, as_userinfo, sess, None)
        self.assertEqual(send.call_count, 0)


class TestBadDingo(TestCase):

    def test_bad_dingo(self):
        bads = [BadDingo, FeatureUnavailable,
                NoSuchBuild, NoSuchTag, NoSuchTarget, NoSuchUser,]

        for cls in bads:
            inst = cls("test")
            self.assertEqual(str(inst), "%s: test" % cls.complaint)


#
# The end.
