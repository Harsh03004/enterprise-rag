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


def extract_webpage_text(
    url: str,
) -> str:
    response = httpx.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
        },
        timeout=20.0,
        follow_redirects=True,
    )

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

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return "\n\n".join(lines)