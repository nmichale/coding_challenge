# Coding Challenge App

A flask app that queries Github and Bitbucket profiles to get public repo metadata.

## Install:

You can use a virtual environment (conda, venv, etc):
```
conda env create -f environment.yml
source activate user-profiles
```

Or just pip install from the requirements file
``` 
pip install -r requirements.txt
```

I added one package to make async http requests: `aiohttp[speedups]`, which is in the requirements.txt. Any other 
libraries should be in the standard library.

## Running the code

### Spin up the service

```
# start up local server
python -m run 
```

### Making Requests

```
curl -i "http://127.0.0.1:5000/health-check"
```

### Making Profile Requests

Here are the examples in the pdf challenge.

#### mailchimp

```
curl -i "http://127.0.0.1:5000/profile?github_org=mailchimp&bitbucket_org=mailchimp"
```

Response:

```json
{
  "languages": {
    "css": 1,
    "dart": 1,
    "java": 1,
    "javascript": 6,
    "kotlin": 1,
    "mustache": 1,
    "objective-c": 2,
    "php": 10,
    "python": 5,
    "ruby": 8,
    "swift": 1
  },
  "repos": {
    "forked": 4,
    "original": 35
  },
  "sources": {
    "bitbucket": 10,
    "github": 29
  },
  "topics": {
    "android-sdk": 1,
    "ecommerce": 2,
    "email-marketing": 2,
    "ios-sdk": 1,
    "kotlin": 1,
    "magento": 2,
    "magento2": 1,
    "mailchimp": 2,
    "mailchimp-sdk": 2,
    "php": 2,
    "sdk": 2,
    "sdk-android": 1,
    "sdk-ios": 1,
    "swift": 1
  },
  "watchers": 8369
}
```

#### pygame

```
curl -i "http://127.0.0.1:5000/profile?github_org=pygame&bitbucket_org=pygame"
```

Response:

```json
{
  "languages": {
    "c": 1,
    "python": 5,
    "ruby": 1
  },
  "repos": {
    "forked": 3,
    "original": 6
  },
  "sources": {
    "github": 9
  },
  "topics": {
    "flask": 1,
    "game-dev": 1,
    "game-development": 1,
    "gamedev": 1,
    "pygame": 2,
    "python": 2,
    "sdl": 1,
    "sdl2": 1,
    "sqlalchemy": 1
  },
  "watchers": 3321
}
```

### Running tests

```
# Uses the unittest library
python -m unittest tests
```

Note: There may be some miscellaneous warnings or unthrown exceptions with this from the asyncio library, but they
can safely be ignored.

## Considerations

- How do you handle versions of external APIs - are some versions better suited to solve
our problem?
    - I just used the recommended versions in the API docs. 
    - For Github, this was achieved by passing the Accept header: 
    `application/vnd.github.v3+json`, and for the in dev topics route `application/vnd.github.mercy-preview+json`.
    - For Bitbucket, 2.0 seemed to be the newest one mentioned.
    - I think hard-coding the versions is okay, as different versions 
    would likely require different code to parse and merge it.
- How do you/would you handle a failed network call to Github/Bitbucket?
    - I am handling a failed network request (anything not status code=200) by passing the content text back to the 
    client and persisting the same status code.
    - Any unexpected exception would give the string of the exception and 500 status (internal server error).
- What do you return to the client?
    - A json object with the pieces of data merged together.
- Which REST verbs and URI structure makes the most sense?
    - I think a GET makes sense for this, because you are not adding, modifying or deleting any data. Plus, all of the 
    requests made to github and bitbucket are GET's too. I thought a route called profile and two request parameters 
    to specify organization names made sense here. If there were more specific filters, 
    I might add extra path variables and parameters. I generally 
    reserve body arguments for POST and PUT requests.
- How efficient is your code?
    - I tried to use as much parallelism as possible using the asyncio and aiohttp libraries (while still being able 
    to code synchronously unlike in the treading module). Since I/O of waiting on 
    external API's lifts the GIL, this makes the multi-threading possible, when it normally is not possible in Python. 
    - The main areas of multithreading would be handling bitbucket and github routines separately and also handling 
    any additional requests where the base response does not include all of the data needed, and just gives you another 
    link. This includes github topics and bitbucket watchers.
    - One way to increase parallelism would be grabbing all pages at once. However, the github API doesn't give the 
    max page, so this was not possible with it -- it would be possible with bitbucket however.
- I could not find anything for Bitbucket in terms of topics.

## What'd I'd like to improve on...

- Object-oriented - structure Github and Bitbucket as classes extending a repo class. I thought this project was just simple 
enough where a functional paradigm would be more readable. If there were more features, classes might make sense.
- Add more routes and additional parameters to routes - this can give anything that hits this API the ability to get a 
 more specific slice they may be looking for.
- Look into asyncio warnings in the unittest library.
- Explore caching the data pulling - drawback is that this may return stale data.
- Require a github token to be passed. I just included mine to make it simple for you guys to test.
- Compare performance against the synchronous requests module.