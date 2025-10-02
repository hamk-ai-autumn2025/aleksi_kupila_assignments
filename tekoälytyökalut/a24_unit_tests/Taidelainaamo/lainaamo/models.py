import datetime
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.db.models import Q


class Work(models.Model):
    """Model representing a work of art in the library system."""

    name = models.CharField(max_length=200)
    artists = models.ManyToManyField("Artist", through="WorkArtist")
    tags = models.ManyToManyField("Tag", through="Join_tag")
    dateField = models.DateField("Date", null=True, blank=True)
    is_available = models.BooleanField("Is available", default=True)
    technique = models.CharField("Technique used", max_length=200)
    width_cm = models.DecimalField(
        "width (cm)", max_digits=5, decimal_places=2
    )
    height_cm = models.DecimalField(
        "height (cm)", max_digits=5, decimal_places=2
    )
    image_url = models.CharField(max_length=200)
    image = models.ImageField(
        upload_to="artwork_images/", blank=True, null=True
    )

    def __str__(self):
        """Return the name of the work."""
        return self.name

    @property
    def artistStr(self):
        """Return a comma-separated string of artist names."""
        return ", ".join(artist.name for artist in self.artists.all())

    @property
    def unavailable_dates(self):
        """List of dates when the artwork is unavailable for borrowing."""
        current_loans = Loan.objects.filter(work=self)
        dates = [
            (loan.loan_start, loan.loan_end)
            for loan in current_loans
        ]
        dates.sort()
        dates_readable = [
            f"{date[0].day}.{date[0].month}.{date[0].year} - "
            f"{date[1].day}.{date[1].month}.{date[1].year}"
            for date in dates
        ]
        return dates_readable

    def is_available_during(self, desired_start, desired_end):
        """Check if the artwork is available during the specified time."""
        overlapping_loans = Loan.objects.filter(work=self).filter(
            Q(loan_start__lt=desired_end) & Q(loan_end__gt=desired_start)
        )
        return not overlapping_loans.exists()


class Loan(models.Model):
    """
    Model representing a loan of a work.

    This might lead to accumulation of loan data if users or works
    are deleted, but the model handles it by setting to null.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )  # Borrower. If user gets deleted, changes to null
    work = models.ForeignKey(
        Work,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )  # Borrowed work. If work gets deleted, changes to null.
    loan_start = models.DateTimeField("Loan start")
    loan_end = models.DateTimeField("Loan end")
    return_time = models.DateTimeField("Return date", null=True, blank=True)

    @property
    def is_late(self):
        """
        Return True if the loan period has ended
        and work hasn't been returned.
        """
        return self.loan_end < timezone.now()

    @property
    def hasnt_started(self):
        """Return True if the loan has not started yet."""
        return not self.loan_start < timezone.now()

    def timeDiff(self, time1, time2):
        """Return time difference in d/h/min format."""
        diff = time1 - time2
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{days} days, {hours} hours, {minutes} minutes"

    @property
    def time_until_end(self):
        """Time until loan end."""
        return self.timeDiff(self.loan_end, timezone.now())

    @property
    def time_until_start(self):
        """Time until loan start."""
        return self.timeDiff(self.loan_start, timezone.now())


class Tag(models.Model):
    """Model representing a tag for works."""

    name = models.CharField(max_length=200)

    def __str__(self):
        """Return the name of the tag."""
        return self.name


class Artist(models.Model):
    """Model representing an artist."""

    name = models.CharField(max_length=200)

    def __str__(self):
        """Return the name of the artist."""
        return self.name


class WorkArtist(models.Model):
    """
    Model representing the many-to-many relationship between work and artist.
    Deleted if either artist or work is deleted.
    """

    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)


class Join_tag(models.Model):
    """
    Model representing the many-to-many relationship between work and tag.
    Deleted if either is removed.
    """

    work = models.ForeignKey(Work, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


@receiver(post_delete, sender=WorkArtist)
def delete_orphaned_works(sender, instance, **kwargs):
    """
    Automatically deletes orphaned works if every artist is deleted.
    """
    if instance.work.artists.count() == 0:
        instance.work.delete()
