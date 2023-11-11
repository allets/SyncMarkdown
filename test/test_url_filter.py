import unittest

from url_filter import ImageUrlFilter, UrlRule


class TestImageUrlFilter(unittest.TestCase):

    def test_set_rules(self):
        rounds = [
            {
                "input": None,
                "expected": [],
            },
            {
                "input": [],
                "expected": [],
            },
            {
                "input": [
                    "https://i.imgur.com/",
                    "!https://i.imgur.com/test/",
                    "!r=https://(test2|test3)\\.imgur\\.com/test/.+",
                    "r=https://(test2|test3)\\.imgur\\.com/.+",
                ],
                "expected": [
                    UrlRule("https://i.imgur.com/", True, False),
                    UrlRule("https://i.imgur.com/test/", False, False),
                    UrlRule("https://(test2|test3)\\.imgur\\.com/test/.+", False, True),
                    UrlRule("https://(test2|test3)\\.imgur\\.com/.+", True, True),
                ],
            },
        ]

        for r in rounds:
            image_filter = ImageUrlFilter(r["input"])
            output = image_filter.rules
            self.assertListEqual(output, r["expected"])

    def test_match_url(self):
        rounds = [
            {
                "input": [
                    "https://i.imgur.com/",
                    "https://i.imgur.com/1",
                ],
                "pattern": "https://i.imgur.com/",
                "is_regexp_pattern": False,
                "expected": [False, True],
            },
            {
                "input": [
                    "https://i.imgur.com/",
                    "https://i.imgur.com/1",
                ],
                "pattern": "https://i.imgur.com",
                "is_regexp_pattern": False,
                "expected": [False, True],
            },
            {
                "input": [
                    "https://i.imgur.com/AbC9.png",
                    "http://localhost/100.png",
                ],
                "pattern": "http://localhost/",
                "is_regexp_pattern": False,
                "expected": [False, True],
            },
            {
                "input": [
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/100.png",
                ],
                "pattern": "https://test1.imgur.com/100.png",
                "is_regexp_pattern": False,
                "expected": [False, True],
            },
            {
                "input": [
                    "https://test2.imgur.com/101.png",
                    "https://test3.imgur.com/101.png",
                    "https://test21imgur.com/101.png",
                ],
                "pattern": "https://(test2|test3)\\.imgur\\.com/.+",
                "is_regexp_pattern": True,
                "expected": [True, True, False],
            },
        ]

        output = []
        for r in rounds:
            output.clear()
            for url in r["input"]:
                output.append(ImageUrlFilter.match(url, r["pattern"], r["is_regexp_pattern"]))
            self.assertListEqual(output, r["expected"])

    def test_filter_url_with_empty_rule(self):
        input = [
            "https://i.imgur.com/AbC9.png",
            "https://i.stack.imgur.com/aBc8.png",
            "https://test1.imgur.com/101.png",
            "https://test1.imgur.com/test/102.png",
            "http://localhost/100.png",
        ]
        rules = []
        output = ImageUrlFilter(rules).filter(input)
        expected = input
        self.assertListEqual(output, expected)

    def test_filter_url_with_only_positive_rules(self):
        input = [
            "https://i.imgur.com/AbC9.png",
            "https://i.stack.imgur.com/aBc8.png",
            "https://test1.imgur.com/101.png",
            "https://test1.imgur.com/test/102.png",
            "http://localhost/100.png",
        ]
        rules = [
            "https://i.imgur.com/",
            "https://test1.imgur.com/",
        ]
        output = ImageUrlFilter(rules).filter(input)
        expected = [
            "https://i.imgur.com/AbC9.png",
            "https://test1.imgur.com/101.png",
            "https://test1.imgur.com/test/102.png",
        ]
        self.assertListEqual(output, expected)

    def test_filter_url_with_only_negative_rules(self):
        input = [
            "https://i.imgur.com/AbC9.png",
            "https://i.stack.imgur.com/aBc8.png",
            "https://test1.imgur.com/101.png",
            "https://test1.imgur.com/test/102.png",
            "http://localhost/100.png",
        ]
        rules = [
            "!https://test1.imgur.com/test/",
            "!http://localhost/",
        ]
        output = ImageUrlFilter(rules).filter(input)
        expected = [
            "https://i.imgur.com/AbC9.png",
            "https://i.stack.imgur.com/aBc8.png",
            "https://test1.imgur.com/101.png",
        ]
        self.assertListEqual(output, expected)

    def test_filter_url_with_positive_and_negative_rules(self):
        rounds = [
            {
                "input": [
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/test/102.png",
                ],
                "rules": [
                    "https://test1.imgur.com/",
                    "!https://test1.imgur.com/test/",
                ],
                "expected": [
                    "https://test1.imgur.com/101.png",
                ],
            },
            {
                "input": [
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/test/102.png",
                ],
                "rules": [
                    "https://test1.imgur.com/test/",
                    "!https://test1.imgur.com/",
                ],
                "expected": [],
            },
            {
                "input": [
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/test/102.png",
                ],
                "rules": [
                    "!https://test1.imgur.com/",
                    "https://test1.imgur.com/test/",
                ],
                "expected": [
                    "https://test1.imgur.com/test/102.png",
                ],
            },
            {
                "input": [
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/test/102.png",
                ],
                "rules": [
                    "!https://test1.imgur.com/test/",
                    "https://test1.imgur.com/",
                ],
                "expected": [
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/test/102.png",
                ],
            },
            {
                "input": [
                    "https://i.imgur.com/AbC9.png",
                    "https://i.stack.imgur.com/aBc8.png",
                    "https://test1.imgur.com/101.png",
                    "https://test1.imgur.com/test/102.png",
                    "http://localhost/100.png",
                ],
                "rules": [
                    "!http://localhost/",
                    "https://i.imgur.com/",
                ],
                "expected": [
                    "https://i.imgur.com/AbC9.png",
                ],
            },
        ]

        for r in rounds:
            output = ImageUrlFilter(r["rules"]).filter(r["input"])
            self.assertListEqual(output, r["expected"])
