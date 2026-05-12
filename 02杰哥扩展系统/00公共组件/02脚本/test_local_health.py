# -*- coding: utf-8 -*-
"""Local health check for the unified WeCom entry service."""

from urllib.error import URLError
from urllib.request import urlopen


HEALTH_URL = "http://127.0.0.1:19310/health"


def main() -> int:
    try:
        with urlopen(HEALTH_URL, timeout=10) as response:
            if response.status == 200:
                print("健康检查通过")
                return 0
    except URLError:
        pass

    print("健康检查失败")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
