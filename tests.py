import unittest

from app.get_data import run_profile, APIError

class TestGetData(unittest.TestCase):

    def test_mailchimp(self):
        """
        Mailchimp test of the run profile code.
        """
        out = run_profile('mailchimp', 'mailchimp')

        self.assertGreater(out['repos']['original'], 0)
        self.assertGreater(out['repos']['forked'], 0)
        self.assertGreater(out['watchers'], 0)
        self.assertGreater(out['languages']['php'], 0)
        self.assertGreater(len(out['topics']), 0)
        self.assertGreater(out['sources']['github'], 0)
        self.assertGreater(out['sources']['bitbucket'], 0)

    def test_pygame(self):
        """
        Pygame test of the run profile code.
        """
        out = run_profile('pygame', 'pygame')

        self.assertGreater(out['repos']['original'], 0)
        self.assertGreater(out['watchers'], 0)
        self.assertGreater(out['languages']['python'], 0)
        self.assertGreater(len(out['topics']), 0)
        self.assertGreater(out['sources']['github'], 0)

    def test_fake_org(self):
        """
        404 response test.
        """
        try:
            run_profile('fake1234556', 'fake1234556')
        except APIError as e:
            self.assertEqual(e.status_code, 404)

if __name__ == '__main__':
    unittest.main()