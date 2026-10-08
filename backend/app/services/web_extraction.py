import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 "
    "(X11; Linux x86_64) "
    "AppleWebKit/537.36 "
    "(KHTML, like Gecko) "
    "Chrome/150.0.0.0 "
    "Safari/537.36"
)


def validate_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Only absolute HTTP and HTTPS URLs are supported.")

    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not supported.")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, parsed.port, type=socket.SOCK_STREAM
        )
    except socket.gaierror as exc:
        raise ValueError("The URL hostname could not be resolved.") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError(
                "URLs pointing to private or local networks are not supported."
            )

    return url


def extract_webpage_text(
    url: str,
) -> str:
    validate_url(url)

    response = httpx.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=20.0,
        follow_redirects=False,
    )

    if response.is_redirect:
        raise ValueError("Redirecting URLs are not supported.")

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "footer",
            "header",
            "aside",
        ]
    ):
        element.decompose()

    text = soup.get_text(
        separator="\n",
    )

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    return "\n\n".join(lines)
