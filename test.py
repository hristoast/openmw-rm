#!/usr/bin/env python3 -Wd
import shutil
import sys

from omwrm.omwrm import check_data_paths, check_openmw_cfg_path, \
    get_content_paths, parse_args, read_openmw_cfg
from tempfile import mkdtemp, mkstemp
from unittest import TestCase, main as test_main


class OpenMwRmTestCase(TestCase):
    def setUp(self):
        self.cfg = "openmw.cfg"
        self.cfg_fake = "/tmp/openmw.cfg"
        self.real_data_path1 = mkdtemp()
        self.real_data_path2 = mkdtemp()
        self.real_data_list = ['data="{}"\n'.format(self.real_data_path1),
                               'data="{}"\n'.format(self.real_data_path2)]
        self.fake_data_path1 = 'data="/tmp/fake1"\n'
        self.fake_data_path2 = 'data="/tmp/fake2"\n'
        self.fake_data_list = [self.fake_data_path1, self.fake_data_path2]
        self.real_content1_name = mkstemp(dir=self.real_data_path1)[1].split('/')[-1]
        self.real_content2_name = mkstemp(dir=self.real_data_path2)[1].split('/')[-1]
        self.real_content1_path = mkstemp(dir=self.real_data_path1)[1]
        self.real_content2_path = mkstemp(dir=self.real_data_path2)[1]
        self.real_content_list = ['content={}\n'.format(self.real_content1_name),
                                  'content={}\n'.format(self.real_content2_name)]
        self.fake_content_list = ['content=fake1\n', 'content=fake2\n']

    def test_check_openmw_cfg_path_exists(self):
        p = check_openmw_cfg_path(self.cfg)
        self.assertTrue(p)

    def test_check_openmw_cfg_path_doesnt_exist(self):
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        with self.assertRaises(SystemExit):
            parse_args(["--file", self.cfg_fake])
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    def test_check_data_paths_real(self):
        real_list_len = len(self.real_data_list)
        checked_data_list_len = len(check_data_paths(self.real_data_list))
        self.assertEqual(real_list_len, checked_data_list_len)

    def test_check_data_paths_fake(self):
        checked_data_list_len = len(check_data_paths(self.fake_data_list))
        self.assertEqual(0, checked_data_list_len)

    def test_get_content_paths_real(self):
        checked_data_path_list = check_data_paths(self.real_data_list)
        real_list_len = len(self.real_content_list)
        gotten_content_list_len = len(get_content_paths(self.real_content_list, checked_data_path_list))
        self.assertEqual(real_list_len, gotten_content_list_len)

    def test_get_content_paths_fake_with_real_data_paths(self):
        checked_data_path_list = check_data_paths(self.real_data_list)
        self.assertEqual(0, len(get_content_paths(self.fake_content_list, checked_data_path_list)))

    def test_read_openmw_cfg_real(self):
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        r = read_openmw_cfg(self.cfg)
        self.assertEqual(r, None)
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    def test_read_openmw_cfg_fake(self):
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')
        with self.assertRaises(SystemExit):
            read_openmw_cfg(self.cfg_fake)
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    def tearDown(self):
        shutil.rmtree(self.real_data_path1)
        shutil.rmtree(self.real_data_path2)


if __name__ == '__main__':
    test_main()
