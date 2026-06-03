from django.test import TestCase
from companies.models import Company

class CompanyModelTests(TestCase):
    def test_slug_is_unique_for_duplicate_names(self):
        company1 = Company.objects.create(name="IT")
        company2 = Company.objects.create(name="IT")
        company3 = Company.objects.create(name="IT")

        self.assertEqual(company1.slug, "it")
        self.assertEqual(company2.slug, "it-1")
        self.assertEqual(company3.slug, "it-2")
        self.assertNotEqual(company1.slug, company2.slug)
        self.assertNotEqual(company2.slug, company3.slug)
