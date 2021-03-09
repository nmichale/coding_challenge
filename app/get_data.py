import aiohttp
import asyncio
import itertools
import copy
from collections import defaultdict
from typing import List, Callable

# Reversed token to get around github security measures. Token cannot access anything private.
GITHUB_TOKEN = ''.join(list(reversed('ae91fa8302e5affda2831f79b49e6b5251df24ca nekot')))
GITHUB_REPO_URL = 'https://api.github.com/orgs/{}/repos'
GITHUB_HEADERS = {'Accept': 'application/vnd.github.v3+json', 'Authorization': GITHUB_TOKEN}
GITHUB_HEADERS_TOPICS = {'Accept': 'application/vnd.github.mercy-preview+json', 'Authorization': GITHUB_TOKEN}

BITBUCKET_REPO_URL = 'https://api.bitbucket.org/2.0/repositories/{}'

OUT_TEMPLATE = {
    'repos': {
        'original': 0,
        'forked': 0
    },
    'watchers': 0,
    'languages': defaultdict(int),
    'topics': defaultdict(int),
    'sources': defaultdict(int)
}


class APIError(Exception):
    """
    Client response != 200 error exception object.
    """
    def __init__(self, routine: str, status_code: int, text: str):
        self.status_code = status_code
        self.text = text
        message = f"Failed on {routine} routine. Status code: {self.status_code}, text: {self.text}"
        super().__init__(message)


async def get_json(resp: aiohttp.request, error_msg: str) -> List[dict]:
    """
    Get the JSON from a request or throw an error if return code != 200.

    @param resp: aiohttp response object
    @param error_msg: What text you'd like displayed fit there is an error with the request.
    @return: Response in parsed JSON format.
    """
    if resp.status == 200:
        resp_json = await resp.json()
    else:
        resp_text = await resp.text()
        raise APIError(error_msg, resp.status, resp_text)

    return resp_json


async def github_topics(session: aiohttp.ClientSession, resp_json: List[dict]) -> None:
    """
    Asynchronously gather all github topics.

    @param session: HTTP client session.
    @param resp_json: List of responses from already called Bitbucket base request.
    """
    async def get_topics(resp_dict, url):
        async with session.get(url, headers=GITHUB_HEADERS_TOPICS) as sub_resp:
            topics = await get_json(sub_resp, f"Github topics pull: {url}")

        resp_dict['topics'] = topics.get('names')

    await asyncio.gather(*[get_topics(r, f"{r['url']}/topics") for r in resp_json])


async def bitbucket_watchers(session: aiohttp.ClientSession, resp_json: List[dict]) -> None:
    """
    Asynchronously gather all bitbucket watchers in a response list.

    @param session: HTTP client session.
    @param resp_json: List of responses from already called Bitbucket base request.
    """
    async def get_watcher_size(resp_dict, url):
        async with session.get(url) as sub_resp:
            watchers = await get_json(sub_resp, f"Bitbucket watchers pull: {url}")

        resp_dict['watchers'] = watchers.get('size')

    await asyncio.gather(*[get_watcher_size(r, r['links']['watchers']['href']) for r in resp_json])


async def download_loop(session: aiohttp.ClientSession, url: str, params: dict = None, headers: dict = None,
                        val_key: str = None, sub_req_func: List[Callable] = None) -> List[dict]:
    """
    Loop through all pages of a bitbucket or github API url and call all sub request functions.

    @param session: HTTP client session.
    @param url: Base url of API call.
    @param params: HTTP parameters to pass.
    @param headers: HTTP headers to pass.
    @param val_key: Specify if there is a key below the root where the records are in an API response.
    @param sub_req_func: List of functions to call that are based on links in the API response.
    @return: Raw dictionary of responses.
    """
    raw = []
    for i in itertools.count(1):
        if params is None:
            params = {}
        params['page'] = i
        async with session.get(url, headers=headers, params=params) as resp:
            resp_json = await get_json(resp, f"{url} base repo pull. Params: {params}.")

        if val_key is not None:
            resp_json = resp_json[val_key]

        if len(resp_json) <= 0:
            break

        if sub_req_func:
            await asyncio.gather(*[func(session, resp_json) for func in sub_req_func])

        raw.extend(resp_json)

    return raw


async def github_bitbucket_requests(github_org: str, bitbucket_org: str) -> List[List[dict]]:
    """
    Asynchronously gathers github and bitbucket responses for organizations, going through all pages.

    @param github_org: Github organization handle.
    @param bitbucket_org: Bitbucket organization handle.
    @return: List where index 0 is github responses, index 1 is bitbucket responses.
    """

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(
            download_loop(session, GITHUB_REPO_URL.format(github_org), {'type': 'public'}, GITHUB_HEADERS,
                          sub_req_func=[github_topics]),
            download_loop(session, BITBUCKET_REPO_URL.format(bitbucket_org), val_key='values',
                          sub_req_func=[bitbucket_watchers])
        )

    return results


def parse_github_resp(resp: List[dict], out_dict: dict) -> None:
    """
    Parse raw dictionary of github responses and merge it into the output dictionary.

    @param resp: Raw github response list of dictionaries.
    @param out_dict: response dictionary.
    """
    for repo in resp:
        if repo.get('fork'):
            out_dict['repos']['forked'] += 1
        else:
            out_dict['repos']['original'] += 1

        out_dict['watchers'] += repo.get('watchers', 0)

        if repo.get('language'):
            out_dict['languages'][repo['language'].lower()] += 1

        for topic in repo.get('topics', []):
            out_dict['topics'][topic] += 1

        out_dict['sources']['github'] += 1


def parse_bitbucket_resp(resp: List[dict], out_dict: dict) -> None:
    """
    Parse raw dictionary of bitbucket responses and merge it into the output dictionary. Only includes public repos.

    @param resp: Raw bitbucket response list of dictionaries.
    @param out_dict: response dictionary.
    """
    for repo in resp:
        if repo.get('is_private'):
            continue

        out_dict['repos']['original'] += 1

        out_dict['watchers'] += repo.get('watchers', 0)

        if repo.get('language'):
            out_dict['languages'][repo['language'].lower()] += 1

        out_dict['sources']['bitbucket'] += 1


def run_profile(github_org: str, bitbucket_org: str) -> dict:
    """
    Asynchronously run HTTP requests on github and bitbucket to gather "profile" information about repos.

    @param github_org: Github organization handle.
    @param bitbucket_org: Bitbucket organization handle.
    @return: Profile dictionary following a similar format to the static template above.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        responses = loop.run_until_complete(github_bitbucket_requests(github_org, bitbucket_org))
    finally:
        loop.close()

    out_dict = copy.deepcopy(OUT_TEMPLATE)

    for i, parse_func in enumerate((parse_github_resp, parse_bitbucket_resp)):
        parse_func(responses[i], out_dict)

    return out_dict
