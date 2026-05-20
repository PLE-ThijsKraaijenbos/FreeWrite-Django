import uuid
from django.conf import settings
from django.db import models

class JournalContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_text = models.TextField()

    class Meta:
        db_table = 'journal_content'


class LetterContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_text = models.TextField()

    class Meta:
        db_table = 'letter_content'


class ChoiceStoryContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_text = models.TextField()
    story_content = models.JSONField()

    class Meta:
        db_table = 'choice_story_content'


class SpeechBubbleContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_text = models.TextField()
    bubbles = models.JSONField()

    class Meta:
        db_table = 'speech_bubble_content'


class BubblePopContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_text = models.TextField()
    thoughts = models.JSONField()

    class Meta:
        db_table = 'bubble_pop_content'


class ScaleContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title_text = models.TextField()
    left_label = models.TextField()
    right_label = models.TextField()

    class Meta:
        db_table = 'scale_content'

class Journey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='journey'
    )

    def __str__(self):
        return str(self.user)

    class Meta:
        db_table = 'journey'

class Phase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.IntegerField()
    title = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'phase'
        ordering = ['order']

class JourneyStep(models.Model):
    class AssignmentType(models.TextChoices):
        JOURNAL = 'journal', 'Journal'
        LETTER = 'letter', 'Letter'
        CHOICE_STORY = 'choice_story', 'Choice Story'
        SPEECH_BUBBLE = 'speech_bubble', 'Speech Bubble'
        BUBBLE_POP = 'bubble_pop', 'Bubble Pop'
        SCALE = 'scale', 'Scale'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phase = models.ForeignKey(Phase, on_delete=models.CASCADE, related_name='steps')
    order = models.IntegerField()
    title = models.TextField()
    description = models.TextField()
    banner_url = models.TextField()
    assignment_type = models.CharField(max_length=20, choices=AssignmentType.choices)
    is_core = models.BooleanField(default=False)
    activation_rules = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    journal_content = models.OneToOneField(
        JournalContent, null=True, blank=True, on_delete=models.SET_NULL, related_name='journey_step'
    )
    letter_content = models.OneToOneField(
        LetterContent, null=True, blank=True, on_delete=models.SET_NULL, related_name='journey_step'
    )
    choice_story_content = models.OneToOneField(
        ChoiceStoryContent, null=True, blank=True, on_delete=models.SET_NULL, related_name='journey_step'
    )
    speech_bubble_content = models.OneToOneField(
        SpeechBubbleContent, null=True, blank=True, on_delete=models.SET_NULL, related_name='journey_step'
    )
    bubble_pop_content = models.OneToOneField(
        BubblePopContent, null=True, blank=True, on_delete=models.SET_NULL, related_name='journey_step'
    )
    scale_content = models.OneToOneField(
        ScaleContent, null=True, blank=True, on_delete=models.SET_NULL, related_name='journey_step'
    )

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'journey_step'
        ordering = ['order']


class JourneyStepProgress(models.Model):
    class Status(models.TextChoices):
        UNAVAILABLE = 'UNAVAILABLE', 'Unavailable'
        AVAILABLE = 'AVAILABLE', 'Available'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    journey = models.ForeignKey(Journey, on_delete=models.CASCADE, related_name='step_progresses')
    step = models.ForeignKey(JourneyStep, on_delete=models.CASCADE, related_name='progresses')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
    )
    bookmarked = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    response_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'journey_step_progress'