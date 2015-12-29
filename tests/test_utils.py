# coding=utf-8
from unittest import TestCase
from distributor import check_dns, check_txt

__author__ = 'm_messiah'


class TestUtils(TestCase):
    def test_check_dns(self):
        self.assertDictEqual(
            {'ns1.google.com': True,
             'ns2.google.com': True,
             'ns3.example.com': False},
            check_dns("google.com",
                      "ns1.google.com;ns2.google.com;ns3.example.com")
        )

    def test_check_txt(self):
        self.assertTupleEqual((0, 0), check_txt("google.com", ""))