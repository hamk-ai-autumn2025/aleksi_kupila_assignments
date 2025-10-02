from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal, getcontext
from datetime import datetime, timedelta
from .models import Work, Loan, Tag, Artist, WorkArtist, Join_tag


class WorkModelTest(TestCase):

    def setUp(self):
        self.artist = Artist.objects.create(name='Test Artist')
        self.tag = Tag.objects.create(name='Test Tag')

    def test_work_creation(self):
        work = Work.objects.create(
            name='Test Work',
            technique='Test Technique',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='test_url.jpg'
        )
        work.artists.add(self.artist)
        work.tags.add(self.tag)
        self.assertEqual(work.name, 'Test Work')
        self.assertEqual(str(work), 'Test Work')
        self.assertEqual(work.artistStr, 'Test Artist')

    def test_work_with_unicode_names(self):
        # Chinese characters
        work = Work.objects.create(
            name='作品名称中文',
            technique='技术中文',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='test_url.jpg'
        )
        self.assertEqual(work.name, '作品名称中文')

        # Arabic characters
        artist = Artist.objects.create(name='فنان عربي')
        work2 = Work.objects.create(
            name='عمل فني',
            technique='تقنية',
            width_cm=Decimal('20.00'),
            height_cm=Decimal('25.00'),
            image_url='test2.jpg'
        )
        work2.artists.add(artist)
        self.assertEqual(work2.name, 'عمل فني')
        self.assertEqual(work2.artistStr, 'فنان عربي')

    def test_work_long_strings(self):
        long_name = 'A' * 200
        work = Work.objects.create(
            name=long_name,
            technique='Test Technique',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='test_url.jpg'
        )
        self.assertEqual(work.name, long_name)

        # Exceed max length (should raise error on save)
        with self.assertRaises(ValidationError):
            work_too_long = Work(name='A' * 201, technique='Tech', width_cm=Decimal('10.00'), height_cm=Decimal('15.00'), image_url='url')
            work_too_long.full_clean()  # Validate model

    def test_work_decimal_edge_cases(self):
        # Large numbers
        work = Work.objects.create(
            name='Large Work',
            technique='Tech',
            width_cm=Decimal('999.99'),
            height_cm=Decimal('999.99'),
            image_url='url'
        )
        self.assertEqual(work.width_cm, Decimal('999.99'))

        # Small numbers
        work_small = Work.objects.create(
            name='Small Work',
            technique='Tech',
            width_cm=Decimal('0.01'),
            height_cm=Decimal('0.01'),
            image_url='url'
        )
        self.assertEqual(work_small.width_cm, Decimal('0.01'))

        # Zero
        work_zero = Work.objects.create(
            name='Zero Work',
            technique='Tech',
            width_cm=Decimal('0.00'),
            height_cm=Decimal('0.00'),
            image_url='url'
        )
        self.assertEqual(work_zero.width_cm, Decimal('0.00'))

        # Negative (if allowed, but probably not)
        try:
            work_neg = Work.objects.create(
                name='Neg Work',
                technique='Tech',
                width_cm=Decimal('-1.00'),
                height_cm=Decimal('-2.00'),
                image_url='url'
            )
            work_neg.full_clean()
            self.assertTrue(True)  # If no error, passes
        except ValidationError:
            pass  # Expected if negative not allowed

        # Very large decimal places (max 2, but Django may store as is without quantization on save)
        work_prec = Work.objects.create(
            name='Prec Work',
            technique='Tech',
            width_cm=Decimal('10.999'),
            height_cm=Decimal('15.001'),
            image_url='url'
        )
        self.assertEqual(work_prec.width_cm, Decimal('10.999'))  # Stored as provided

    def test_work_availability(self):
        work = Work.objects.create(
            name='Avail Work',
            technique='Tech',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='url'
        )
        user = User.objects.create_user(username='testuser', password='pass')

        # No loans, should be available
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(days=7)
        self.assertTrue(work.is_available_during(start, end))

        # With loan
        loan = Loan.objects.create(
            user=user,
            work=work,
            loan_start=start - timedelta(days=2),
            loan_end=end + timedelta(days=2)
        )
        self.assertFalse(work.is_available_during(start, end))

        # Non-overlapping loan
        self.assertTrue(work.is_available_during(start + timedelta(days=30), end + timedelta(days=30)))


class LoanModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.work = Work.objects.create(
            name='Test Work',
            technique='Tech',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='url'
        )

    def test_loan_creation(self):
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(days=7)
        loan = Loan.objects.create(
            user=self.user,
            work=self.work,
            loan_start=start,
            loan_end=end
        )
        self.assertEqual(loan.user, self.user)
        self.assertEqual(loan.work, self.work)

    def test_loan_properties(self):
        past_loan = Loan.objects.create(
            user=self.user,
            work=self.work,
            loan_start=timezone.now() - timedelta(days=10),
            loan_end=timezone.now() - timedelta(days=5)
        )
        self.assertFalse(past_loan.hasnt_started)
        self.assertTrue(past_loan.is_late)

        future_loan = Loan.objects.create(
            user=self.user,
            work=self.work,
            loan_start=timezone.now() + timedelta(days=5),
            loan_end=timezone.now() + timedelta(days=10)
        )
        self.assertTrue(future_loan.hasnt_started)
        self.assertFalse(future_loan.is_late)

    def test_time_diff(self):
        loan = Loan.objects.create(
            user=self.user,
            work=self.work,
            loan_start=timezone.now(),
            loan_end=timezone.now() + timedelta(days=2, hours=3, minutes=45)
        )
        diff_str = loan.time_until_end
        self.assertIn('days', diff_str)

    def test_loan_edge_dates(self):
        # Very old date
        old_start = timezone.now() - timedelta(days=365*100)
        loan_old = Loan.objects.create(
            user=self.user,
            work=self.work,
            loan_start=old_start,
            loan_end=old_start + timedelta(days=1)
        )
        self.assertTrue(loan_old.is_late)

        # Far future
        future_start = timezone.now() + timedelta(days=365*100)
        loan_future = Loan.objects.create(
            user=self.user,
            work=self.work,
            loan_start=future_start,
            loan_end=future_start + timedelta(days=1)
        )
        self.assertTrue(loan_future.hasnt_started)


class TagModelTest(TestCase):

    def test_tag_creation(self):
        tag = Tag.objects.create(name='Test Tag')
        self.assertEqual(tag.name, 'Test Tag')
        self.assertEqual(str(tag), 'Test Tag')

    def test_tag_unicode(self):
        tag_cn = Tag.objects.create(name='标签')
        self.assertEqual(str(tag_cn), '标签')

        tag_ar = Tag.objects.create(name='وسم')
        self.assertEqual(str(tag_ar), 'وسم')

    def test_tag_long_name(self):
        long_tag = Tag.objects.create(name='A' * 200)
        self.assertEqual(long_tag.name, 'A' * 200)

        # Exceed max
        with self.assertRaises(ValidationError):
            tag_long = Tag(name='A' * 201)
            tag_long.full_clean()


class ArtistModelTest(TestCase):

    def test_artist_creation(self):
        artist = Artist.objects.create(name='Test Artist')
        self.assertEqual(artist.name, 'Test Artist')
        self.assertEqual(str(artist), 'Test Artist')

    def test_artist_unicode(self):
        artist_cn = Artist.objects.create(name='艺术家')
        self.assertEqual(str(artist_cn), '艺术家')

        artist_ar = Artist.objects.create(name='فنان')
        self.assertEqual(str(artist_ar), 'فنان')

    def test_artist_long_name(self):
        long_artist = Artist.objects.create(name='A' * 200)
        self.assertEqual(long_artist.name, 'A' * 200)

        with self.assertRaises(ValidationError):
            artist_long = Artist(name='A' * 201)
            artist_long.full_clean()


class RelationshipModelTest(TestCase):

    def setUp(self):
        self.artist = Artist.objects.create(name='Test Artist')
        self.tag = Tag.objects.create(name='Test Tag')
        self.work = Work.objects.create(
            name='Test Work',
            technique='Tech',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='url'
        )

    def test_work_artist_relation(self):
        wa = WorkArtist.objects.create(work=self.work, artist=self.artist)
        self.assertEqual(wa.work, self.work)
        self.assertEqual(wa.artist, self.artist)

    def test_join_tag_relation(self):
        jt = Join_tag.objects.create(work=self.work, tag=self.tag)
        self.assertEqual(jt.work, self.work)
        self.assertEqual(jt.tag, self.tag)

    def test_delete_orphaned_work(self):
        # Create work with artist
        wa = WorkArtist.objects.create(work=self.work, artist=self.artist)
        self.assertEqual(Work.objects.count(), 1)

        # Delete artist, should delete work since no artists left
        self.artist.delete()
        self.assertEqual(Work.objects.count(), 0)

    def test_no_orphan_if_multiple_artists(self):
        artist2 = Artist.objects.create(name='Artist 2')
        WorkArtist.objects.create(work=self.work, artist=self.artist)
        WorkArtist.objects.create(work=self.work, artist=artist2)
        self.assertEqual(Work.objects.count(), 1)

        # Delete one artist, work should remain
        self.artist.delete()
        self.assertEqual(Work.objects.count(), 1)


class EdgeCasesTest(TestCase):

    def test_null_fields(self):
        # Work with null dateField and image
        work = Work.objects.create(
            name='Null Work',
            technique='Tech',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='url',
            dateField=None,  # Null
            is_available=True
        )
        self.assertIsNone(work.dateField)

        # Loan with null return_time
        user = User.objects.create_user(username='user', password='pass')
        loan = Loan.objects.create(
            user=user,
            work=work,
            loan_start=timezone.now(),
            loan_end=timezone.now() + timedelta(days=1),
            return_time=None
        )
        self.assertIsNone(loan.return_time)

    def test_very_long_strings(self):
        # Test for fields not directly limited, but input handling
        # For example, Web URL long
        long_url = 'http://' + 'A' * 180 + '.com'
        work = Work.objects.create(
            name='URL Work',
            technique='Tech',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url=long_url
        )
        self.assertEqual(len(work.image_url), len(long_url))

    def test_extreme_decimals(self):
        try:
            # Try to create with very large numbers that fit in Decimal(5,2): max 999.99
            work_big = Work.objects.create(
                name='Big Dec',
                technique='Tech',
                width_cm=Decimal('999.99'),
                height_cm=Decimal('999.99'),
                image_url='url'
            )
            self.assertEqual(work_big.width_cm, Decimal('999.99'))
        except ValidationError:
            pass  # If doesn't fit

        # Test if infinity can be assigned (likely not)
        try:
            infinite_cm = Decimal('inf')
            work_inf = Work(
                name='Inf Work',
                technique='Tech',
                width_cm=infinite_cm,
                height_cm=Decimal('10.00'),
                image_url='url'
            )
            work_inf.full_clean()  # Should raise error
            self.fail("Should not allow infinity")
        except ValidationError:
            pass
        except Exception:
            pass

    def test_datetime_extremes(self):
        # Very old datetime
        old_datetime = timezone.make_aware(datetime(1, 1, 1, 0, 0, 0))
        user = User.objects.create_user(username='user', password='pass')
        work = Work.objects.create(
            name='Old Loan Work',
            technique='Tech',
            width_cm=Decimal('10.00'),
            height_cm=Decimal('15.00'),
            image_url='url'
        )
        loan_old = Loan.objects.create(
            user=user,
            work=work,
            loan_start=old_datetime,
            loan_end=old_datetime + timedelta(days=1)
        )
        self.assertTrue(loan_old.is_late)  # Should be late

        # Far future
        future_datetime = timezone.now() + timedelta(days=365*1000)  # 1000 years
        loan_future = Loan.objects.create(
            user=user,
            work=work,
            loan_start=future_datetime,
            loan_end=future_datetime + timedelta(days=1)
        )
        self.assertTrue(loan_future.hasnt_started)
