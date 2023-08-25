from django.core import mail
from django.test import TestCase

from bitu import utils


class UtilsEmailTest(TestCase):
    subject = 'test service message'
    body = 'test message body'

    def test_sending_service_email(self):
        with self.settings(ADMINS=['admin@example.com',]):
            utils.send_service_message(self.subject,
                                       self.body)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'[BITU] {self.subject}')


    def test_no_admin(self):
        utils.send_service_message(self.subject, self.body)
        self.assertEqual(len(mail.outbox), 0)

        utils.send_service_message(self.subject, self.body, limited=True)
        self.assertEqual(len(mail.outbox), 0)

        mail.outbox = []
        with self.settings(ADMINS_LIMITED=[], ADMINS=['admin@example.com',]):
            utils.send_service_message(self.subject, self.body, limited=True)
            self.assertEqual(len(mail.outbox), 0)

        mail.outbox = []
        with self.settings(ADMINS_LIMITED=['admin@example.org']):
            utils.send_service_message(self.subject, self.body, limited=True)
            self.assertEqual(len(mail.outbox), 1)

        mail.outbox = []
        with self.settings(ADMINS=['admin@example.org']):
            utils.send_service_message(self.subject, self.body, limited=True)
            self.assertEqual(len(mail.outbox), 1)



    def test_sending_limited_service_email(self):

        with self.settings(ADMINS_LIMITED=['admin@example.net',],
                           ADMINS=['admin@example.com',]):

            utils.send_service_message(self.subject,
                                       self.body)

            utils.send_service_message(self.subject,
                                       self.body,
                                       limited=True)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, ['admin@example.net',])
        mail.outbox = []

        with self.settings(ADMINS=['admin@example.com',]):
            utils.send_service_message(self.subject,
                                       self.body,
                                       limited=True)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].to, ['admin@example.com',])
