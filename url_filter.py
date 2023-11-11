import logging
import os
import re
import sys
from typing import List

from data_base_class import DataPrintable

LOG_DIR = f"{os.path.dirname(os.path.abspath(__file__))}/log"
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

LOGGING_FORMAT = "%(asctime)s %(levelname)s: %(message)s"
logging.basicConfig(level=logging.DEBUG,
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler(f"{LOG_DIR}/{os.path.splitext(os.path.basename(__file__))[0]}.log",
                                            "w", "utf-8")
                    ],
                    format=LOGGING_FORMAT)


class UrlRule(DataPrintable):
    def __init__(self, pattern, is_positive, is_regexp):
        self.pattern = pattern
        self.is_positive = is_positive
        self.is_regexp = is_regexp

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        for k, v in self.__dict__.items():
            if v != other.__dict__[k]:
                return False

        return True

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))


class ImageUrlFilter:
    rules: List[UrlRule] = []

    def __init__(self, rules: List[str]):
        self.set_rules(rules)

    def set_rules(self, rules):
        """
        User defines rules to limit which images can be downloaded.
        A filter without any rules allows all images to be downloaded.

        A rule can be positive or negative.
        Positive rules allow the defined images to be downloaded.
        For example::

            https://test1.imgur.com/
            https://test2.imgur.com/

        Negative rules start with `!` and prevent the defined images from being downloaded.
        For example::

            !http://localhost/
            !https://test2.imgur.com/10
            !https://test2.imgur.com/Xxx.png

        The pattern of a rule can be a regular expression and preceded by `r=`.
        For example::

            r=https://(test1|test2)\.imgur\.com/.+
            !r=https://test2\.imgur\.com/(10.+|Xxx\.png)

        The later rule takes precedence.
        For example, the filter with the following rules forbids images
        from "https://test1.imgur.com/" to be downloaded. ::

            https://test1.imgur.com/
            !https://test1.imgur.com/
        """
        self.rules.clear()
        if rules is None:
            rules = []

        for rule in rules:
            rule = rule.strip()

            is_positive = (rule[0] != "!")
            pattern = rule if is_positive else rule[1:]

            is_regexp = (pattern[:2] == "r=")
            pattern = pattern[2:] if is_regexp else pattern

            self.rules.append(UrlRule(pattern, is_positive, is_regexp))

        # logging.debug(f"rules= [{','.join([str(r) for r in self.rules])}]")

    @staticmethod
    def match(url, pattern, is_regexp=False):
        if is_regexp:
            if re.match(pattern, url):
                return True
        else:
            if url.startswith(pattern) and not url.endswith("/"):
                return True

        return False

    def is_ok(self, url):
        if not self.rules:
            return True

        isOk = False
        set_by_positive_rule = None
        for rule in self.rules:
            is_match = self.match(url, rule.pattern, rule.is_regexp)
            if is_match:
                isOk = rule.is_positive
                set_by_positive_rule = rule.is_positive
            else:
                if rule.is_positive:  # not ok: not follow the positive rule
                    if isOk:
                        if set_by_positive_rule is None:
                            isOk = False
                            set_by_positive_rule = rule.is_positive
                        elif set_by_positive_rule:
                            # The previous rule takes precedence.
                            pass
                        else:
                            isOk = False
                            set_by_positive_rule = rule.is_positive
                    else:
                        if set_by_positive_rule is None:
                            set_by_positive_rule = rule.is_positive
                        elif set_by_positive_rule:
                            pass
                        else:
                            # The previous rule takes precedence.
                            pass
                else:  # ok: follow the negative rule
                    if isOk:
                        if set_by_positive_rule is None:
                            set_by_positive_rule = rule.is_positive
                        elif set_by_positive_rule:
                            # The previous rule takes precedence.
                            pass
                        else:
                            pass
                    else:
                        if set_by_positive_rule is None:
                            isOk = True
                            set_by_positive_rule = rule.is_positive
                        elif set_by_positive_rule:
                            # The previous rule takes precedence.
                            pass
                        else:
                            # The previous rule takes precedence.
                            pass

        return isOk

    def filter(self, urls) -> List[str]:
        output = []
        for url in urls:
            if self.is_ok(url):
                output.append(url)
        return output
