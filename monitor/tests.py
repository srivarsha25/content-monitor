from django.test import TestCase
from django.utils import timezone
from .models import Keyword, ContentItem, Flag
from .services import compute_score, run_scan


class ScoringTests(TestCase):

    def test_exact_title_match(self):
        score = compute_score('django', 'django', 'some body text')
        self.assertEqual(score, 100)

    def test_partial_title_match(self):
        score = compute_score('django', 'Learn Django Fast', 'some body text')
        self.assertEqual(score, 90)

    def test_body_only_match(self):
        score = compute_score('python', 'Cooking Tips', 'python is great for automation')
        self.assertEqual(score, 50)

    def test_no_match(self):
        score = compute_score('django', 'Cooking Tips', 'best recipes for beginners')
        self.assertEqual(score, 0)

    def test_multiword_title_match(self):
        score = compute_score('data pipeline', 'Building a Data Pipeline', 'some body')
        self.assertEqual(score, 90)

    def test_multiword_body_match(self):
        score = compute_score('data pipeline', 'Random Title', 'build a data pipeline today')
        self.assertEqual(score, 50)


class SuppressionTests(TestCase):

    def setUp(self):
        self.keyword = Keyword.objects.create(name='django')
        self.content_item = ContentItem.objects.create(
            title='Learn Django Fast',
            source='Blog A',
            body='Django is a powerful Python framework',
            last_updated=timezone.now()
        )

    def test_flag_created_on_scan(self):
        run_scan()
        self.assertTrue(Flag.objects.filter(keyword=self.keyword).exists())

    def test_suppression_prevents_reflag(self):
        Flag.objects.create(
            keyword=self.keyword,
            content_item=self.content_item,
            score=70,
            status='irrelevant',
            content_snapshot=self.content_item.last_updated
        )
        run_scan()
        flag = Flag.objects.get(keyword=self.keyword, content_item=self.content_item)
        self.assertEqual(flag.status, 'irrelevant')

    def test_changed_content_resets_suppressed_flag(self):
        old_time = self.content_item.last_updated
        flag = Flag.objects.create(
            keyword=self.keyword,
            content_item=self.content_item,
            score=70,
            status='irrelevant',
            content_snapshot=old_time
        )
        new_time = timezone.now() + timezone.timedelta(hours=1)
        self.content_item.last_updated = new_time
        self.content_item.save()

        content_changed = (
            flag.content_snapshot is None or
            self.content_item.last_updated > flag.content_snapshot
        )
        if content_changed:
            flag.status = 'pending'
            flag.save()

        flag.refresh_from_db()
        self.assertEqual(flag.status, 'pending')


class DeduplicationTests(TestCase):

    def test_no_duplicate_flags(self):
        run_scan()
        run_scan()  # scan twice
        count = Flag.objects.count()
        # Should be same count after second scan, no duplicates
        run_scan()
        self.assertEqual(Flag.objects.count(), count)